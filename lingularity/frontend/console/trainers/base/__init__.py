from typing import Optional, Tuple, Type, Iterator
from abc import ABC, abstractmethod
import time
import datetime

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
from pynput.keyboard import Controller as KeyboardController

from lingularity.utils import either
from lingularity.backend.trainers import TrainerBackend
from lingularity.backend.components import VocableEntry
from lingularity.backend.metadata import language_metadata
from lingularity.backend.database import MongoDBClient
from lingularity.backend.utils import date as date_utils

from lingularity.frontend.console.utils.output import RedoPrint, centered_print
from lingularity.frontend.console.utils import matplotlib as plt_utils
from .options import TrainingOptions


class TrainerConsoleFrontend(ABC):
    SELECTION_QUERY_OUTPUT_OFFSET = '\n\t'

    def __init__(self, backend: Type[TrainerBackend], mongodb_client: MongoDBClient):
        non_english_language, train_english = self._select_training_language(mongodb_client)
        self._backend: TrainerBackend = backend(non_english_language, train_english, mongodb_client)

        self._buffer_print: RedoPrint = RedoPrint()
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
    def __call__(self) -> bool:
        """ Invokes trainer frontend

            Returns:
                reinitialize program flag: bool """
        pass

    # -----------------
    # Pre Training
    # -----------------
    @abstractmethod
    def _select_training_language(self, mongodb_client: Optional[MongoDBClient] = None) -> Tuple[str, bool]:
        pass

    @abstractmethod
    def _display_training_screen_header_section(self):
        pass

    def _output_lets_go(self):
        centered_print(either(language_metadata[self._backend.language]['translations'].get('letsGo'), default="Let's go!"), '\n' * 2)

    # -----------------
    # Training
    # -----------------
    @abstractmethod
    def _run_training(self):
        pass

    def _add_vocable(self) -> int:
        """ Returns:
                number of printed lines: int """

        vocable_and_meaning = [None, None]
        query_messages = [f'Enter {self._backend.language} word/phrase: ', 'Enter meaning(s): ']

        for i, query_message in enumerate(query_messages):
            vocable_and_meaning[i] = input(query_message)
            if not len(vocable_and_meaning[i]):
                centered_print("Input field left unfilled")
                time.sleep(1)
                return 3

        self._latest_created_vocable_entry = VocableEntry.new(*vocable_and_meaning)
        self._backend.mongodb_client.insert_vocable(self._latest_created_vocable_entry)

        return 2

    def _alter_vocable_entry(self, vocable_entry: VocableEntry) -> int:
        """ Returns:
                number of printed lines: int """

        old_line_repr = vocable_entry.line_repr
        KeyboardController().type(f'{old_line_repr}')
        new_entry_components = input('').split(' - ')

        if len(new_entry_components) != 2:
            centered_print('Invalid alteration')
            time.sleep(1)
            return 3

        old_vocable = vocable_entry.token
        vocable_entry.alter(*new_entry_components)

        if vocable_entry.line_repr != old_line_repr:
            self._backend.mongodb_client.insert_altered_vocable_entry(old_vocable, vocable_entry)

        return 2

    # -----------------
    # Post Training
    # -----------------
    def _plot_training_chronic(self):
        DAY_DELTA = 14

        plt.style.use('dark_background')

        TRAINER_INDEX = str(self) == 'v'

        # query language training history
        training_history = self._backend.mongodb_client.query_training_chronic()
        training_history = {date: trainer_dict[str(self)] for date, trainer_dict in training_history.items() if trainer_dict.get(str(self))}

        # get plotting dates
        dates = list(self._get_plotting_dates(training_dates=iter(training_history.keys()), day_delta=DAY_DELTA))

        # query number of trained sentences, vocabulary entries at every stored date,
        # pad item values of asymmetrically item-value-beset dates
        training_item_sequence = [training_history.get(date, 0) for date in dates]

        # omit year, invert day & month for proper tick label display, replace todays date with 'today'
        dates = ['-'.join(date.split('-')[1:][::-1]) for date in dates[:-1]] + ['today']

        if len(dates) == 1:
            dates = ['a.l.'] + dates
            training_item_sequence = [0] + training_item_sequence

        # set up figure
        fig, ax = plt.subplots()
        fig.set_size_inches(np.asarray([6.5, 7]))
        fig.canvas.draw()
        fig.canvas.set_window_title("Way to go!")

        # define plot
        ax.set_title(f'{self._backend.language} Training History')

        max_value_training_item = max(training_item_sequence)
        x_range = np.arange(len(dates))

        ax.plot(x_range, training_item_sequence, marker=None, markevery=list(x_range), color=['r', 'b'][TRAINER_INDEX], linestyle='solid', label='sentences')

        ax.set_xticks(x_range)
        ax.set_xticklabels(dates, minor=False, rotation=45)
        ax.set_xlabel('date')
        ax.set_xlim(left=0, right=len(x_range) + (DAY_DELTA / 2) * (1 - len(x_range) / DAY_DELTA))

        ax.set_ylim(bottom=0, top=max_value_training_item + max_value_training_item * 0.3)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_ylabel(['# trained sentences', '# trained vocabulary'][TRAINER_INDEX])

        plt_utils.center_windows()
        plt.show(block=False)
        plt.waitforbuttonpress(timeout=0)

    @staticmethod
    def _get_plotting_dates(training_dates: Iterator[str], day_delta: int) -> Iterator[str]:
        starting_date = TrainerConsoleFrontend._get_starting_date(training_dates, day_delta)

        while starting_date <= date_utils.today:
            yield str(starting_date)
            starting_date += datetime.timedelta(days=1)

    @staticmethod
    def _get_starting_date(training_dates: Iterator[str], day_delta: int) -> datetime.date:
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
