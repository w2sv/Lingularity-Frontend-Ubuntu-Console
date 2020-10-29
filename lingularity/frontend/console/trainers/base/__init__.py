from typing import Optional, Type, Iterator, Sequence, overload, Union
from abc import ABC, abstractmethod
from time import sleep
import datetime

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
from pynput.keyboard import Controller as KeyboardController

from lingularity.utils import either
from lingularity.backend.trainers import *
from lingularity.backend.components import VocableEntry
from lingularity.backend.metadata import language_metadata
from lingularity.backend.utils import date as date_utils

from lingularity.frontend.console.reentrypoint import ReentryPoint
from lingularity.frontend.console.state import State
from lingularity.frontend.console.utils import output, matplotlib as plt_utils, view
from .options import TrainingOptions


TrainerBackendType = Union[
    Type[SentenceTranslationTrainerBackend],
    Type[VocableTrainerBackend],
    Type[VocableAdderBackend]
]


@overload
def _backend(backend_type: Type[VocableTrainerBackend]) -> VocableTrainerBackend: ...
@overload
def _backend(backend_type: Type[SentenceTranslationTrainerBackend]) -> SentenceTranslationTrainerBackend: ...
@overload
def _backend(backend_type: Type[VocableAdderBackend]) -> VocableAdderBackend: ...


def _backend(backend_type: TrainerBackendType) -> Union[VocableTrainerBackend, SentenceTranslationTrainerBackend, VocableAdderBackend]:
    return backend_type(State.non_english_language, State.train_english)


class TrainerFrontend(ABC):
    def __init__(self, backend_type: TrainerBackendType):
        self._backend = _backend(backend_type=backend_type)

        self._training_options: TrainingOptions = self._get_training_options()

        self._n_trained_items: int = 0
        self._latest_created_vocable_entry: Optional[VocableEntry] = None

    @abstractmethod
    def _get_training_options(self) -> TrainingOptions:
        pass

    # -----------------
    # Driver
    # -----------------
    @abstractmethod
    def __call__(self) -> ReentryPoint:
        """ Invokes trainer frontend

            Returns:
                reentry point """
        pass

    def _set_terminal_title(self):
        view.set_terminal_title(f'{self._backend.language} {self._training_designation}')

    @property
    @abstractmethod
    def _training_designation(self) -> str:
        pass

    # -----------------
    # Pre Training
    # -----------------
    @abstractmethod
    def _display_training_screen_header_section(self):
        pass

    def _output_lets_go(self):
        output.centered_print(either(language_metadata[self._backend.language]['translations'].get('letsGo'), default="Let's go!"), '\n' * 2)

    # -----------------
    # Training
    # -----------------
    @abstractmethod
    def _run_training_loop(self):
        pass

    def _add_vocable(self) -> int:
        """ Returns:
                number of printed lines: int """

        INDENTATION = output.column_percentual_indentation(percentage=0.32)

        vocable_and_meaning = []

        for query_message in [f'Enter {self._backend.language} word/phrase: ', 'Enter meaning(s): ']:
            if not len((field := input(f'{INDENTATION}{query_message}'))):
                output.centered_print("INPUT FIELD LEFT UNFILLED")
                sleep(1)
                return 3
            vocable_and_meaning.append(field)

        self._latest_created_vocable_entry = VocableEntry.new(*vocable_and_meaning)
        self._backend.mongodb_client.insert_vocable_entry(self._latest_created_vocable_entry)

        return 2

    def _alter_vocable_entry(self, vocable_entry: VocableEntry) -> int:
        """ Returns:
                number of printed lines: int """

        # store old properties for comparison, database identification
        old_line_repr = str(vocable_entry)
        old_vocable = vocable_entry.vocable

        # type indented old representation
        KeyboardController().type(f'{output.centered_print_indentation(old_line_repr)}{old_line_repr}')
        # TODO: debug print(centering_indentation) into KeyboardController().type(old_line_repr)

        # get new components, i.e. vocable + ground_truth
        new_entry_components = input('').split(' - ')

        # exit in case of invalid alteration
        if len(new_entry_components) != 2:
            output.centered_print('INVALID ALTERATION')
            sleep(1)
            return 3

        # strip whitespaces, alter vocable entry
        stripped_new_entry_components = map(lambda component: component.strip(' '), new_entry_components)
        vocable_entry.alter(*stripped_new_entry_components)

        # insert altered entry into database in case of alteration actually having taken place
        if str(vocable_entry) != old_line_repr:
            self._backend.mongodb_client.alter_vocable_entry(old_vocable, vocable_entry)

        return 2

    # -----------------
    # Post Training
    # -----------------
    def _plot_training_chronic(self):
        DAY_DELTA = 14

        plt.style.use('dark_background')

        # query language training history of respective trainer
        training_history = self._backend.mongodb_client.query_training_chronic()
        training_history = {date: trainer_dict[str(self)] for date, trainer_dict in training_history.items() if trainer_dict.get(str(self))}

        # get plotting dates
        dates = list(self._plotting_dates(training_dates=iter(training_history.keys()), day_delta=DAY_DELTA))
        # get training item sequence, conduct zero-padding on dates on which no training took place
        item_scores = [training_history.get(date, 0) for date in dates]

        # omit year, invert day & month for proper tick label display, replace todays date with 'today'
        dates = ['-'.join(date.split('-')[1:][::-1]) for date in dates[:-1]] + ['today']

        # add 0 y-value in case of only one y-value being present
        if len(dates) == 1:
            dates = ['a.l.'] + dates
            item_scores = [0] + item_scores

        # set up figure
        fig, ax = plt.subplots()
        # fig.set_size_inches(np.asarray([6.5, 7]))
        fig.canvas.draw()
        fig.canvas.set_window_title(f'{self._backend.language} Training History')

        ax.set_title(self._training_chronic_axis_title(item_scores), c='darkgoldenrod', fontsize=11)

        # define plot
        x_range = np.arange(len(dates))

        ax.plot(x_range, item_scores, marker=None, markevery=list(x_range), color=['r', 'b'][str(self) == 'v'], linestyle='solid', label='sentences')
        ax.set_xticks(x_range)
        ax.set_xticklabels(dates, minor=False, rotation=45)
        ax.set_xlabel('date')
        # set margin between left axis and first y-value to 0, shift plot towards left depending
        # on sparseness of available number of dates with small amount of dates -> vast shift
        ax.set_xlim(left=0, right=len(x_range) + (DAY_DELTA / 2) * (1 - len(x_range) / DAY_DELTA))

        max_value_item_score = max(item_scores)
        # leave space between biggest y-value and plot top
        ax.set_ylim(bottom=0, top=max_value_item_score + max_value_item_score * 0.3)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_ylabel(f'# trained {self._pluralized_item_name}')

        plt_utils.center_window()
        plt_utils.close_window_on_button_press()

    def _training_chronic_axis_title(self, item_scores: Sequence[int]) -> str:
        if len(item_scores) == 2 and not item_scores[0]:
            return "Let's get that graph inflation goin'"

        yesterday_exceedance_difference = item_scores[-1] - item_scores[-2] + 1
        item_name = [self._pluralized_item_name, self._item_name][yesterday_exceedance_difference in [-1, 0]]

        if yesterday_exceedance_difference >= 0:
            return f"Exceeded yesterdays score by {yesterday_exceedance_difference + 1} {item_name}"
        return f"{abs(yesterday_exceedance_difference)} {item_name} left to top yesterdays score"

    @property
    @abstractmethod
    def _pluralized_item_name(self) -> str:
        pass

    @property
    @abstractmethod
    def _item_name(self) -> str:
        pass

    @staticmethod
    def _plotting_dates(training_dates: Iterator[str], day_delta: int) -> Iterator[str]:
        """ Returns:
                continuous sequence of plotting dates to be seized as x-axis ticks
                starting from earliest day with (todays date - respective date) <= day_delta,
                going up to todays date

        e.g.:

            today = '2020-10-20'
            training_dates = ('2020-07-19', '2020-08-05', '2020-08-10', '2020-08-12', '2020-08-13', '2020-08-14',
            '2020-08-15', '2020-08-16', '2020-09-18', '2020-09-19', '2020-09-20', '2020-09-21', '2020-09-22',
            '2020-09-24', '2020-09-25', '2020-09-26', '2020-09-27', '2020-09-28', '2020-09-29', '2020-09-30',
            '2020-10-06', '2020-10-12', '2020-10-13', '2020-10-14', '2020-10-15', '2020-10-16', '2020-10-17',
            '2020-10-19', '2020-10-20')

            TrainerFrontend._plotting_dates(_training_dates, day_delta=14)
            ['2020-10-06', '2020-10-07', '2020-10-08', '2020-10-09', '2020-10-10', '2020-10-11', '2020-10-12',
            '2020-10-13', '2020-10-14', '2020-10-15', '2020-10-16', '2020-10-17', '2020-10-18', '2020-10-19',
            '2020-10-20'] """

        starting_date = TrainerFrontend._get_starting_date(training_dates, day_delta)

        while starting_date <= date_utils.today:
            yield str(starting_date)
            starting_date += datetime.timedelta(days=1)

    @staticmethod
    def _get_starting_date(training_dates: Iterator[str], day_delta: int) -> datetime.date:
        """ Returns:
                earliest date comprised within training_dates for which (todays date - respective date) <= day_delta
                holds true """

        earliest_possible_date: datetime.date = (date_utils.today - datetime.timedelta(days=day_delta))

        for training_date in training_dates:
            if (converted_date := date_utils.string_2_date(training_date)) >= earliest_possible_date:
                return converted_date

        raise AttributeError

    # -----------------
    # Dunder(s)
    # -----------------
    def __str__(self):
        return self.__class__.__name__[0].lower()
