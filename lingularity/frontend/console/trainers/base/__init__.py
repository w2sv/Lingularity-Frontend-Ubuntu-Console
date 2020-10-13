from typing import Optional, Tuple, Type
from abc import ABC, abstractmethod
import time

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
from pynput.keyboard import Controller as KeyboardController

from lingularity.backend.trainers import TrainerBackend
from lingularity.backend.components import VocableEntry
from lingularity.backend.metadata import language_metadata
from lingularity.backend.database import MongoDBClient

from lingularity.frontend.console.utils.output import BufferPrint, centered_print
from lingularity.frontend.console.utils.matplotlib import center_matplotlib_windows
from .options import TrainingOptions


class TrainerConsoleFrontend(ABC):
    SELECTION_QUERY_OUTPUT_OFFSET = '\n\t'

    def __init__(self, backend: Type[TrainerBackend], mongodb_client: MongoDBClient):
        non_english_language, train_english = self._select_training_language(mongodb_client)
        self._backend: TrainerBackend = backend(non_english_language, train_english, mongodb_client)

        self._buffer_print: BufferPrint = BufferPrint()
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
    def _display_training_screen_header(self):
        pass

    def _output_lets_go(self):
        centered_print(language_metadata[self._backend.language]['translations']['letsGo'] or "Let's go!", '\n' * 2)

    # -----------------
    # Training
    # -----------------
    @abstractmethod
    def _run_training(self):
        pass

    def _add_vocable(self) -> int:
        """ Returns:
                number of printed lines """

        vocable = input(f'Enter {self._backend.language} word/phrase: ')
        meanings = input('Enter meaning(s): ')

        if not all([vocable, meanings]):
            centered_print("Input field left unfilled")
            time.sleep(1)
            return 3

        self._latest_created_vocable_entry = VocableEntry.new(vocable, meanings)
        self._backend.mongodb_client.insert_vocable(self._latest_created_vocable_entry)

        return 2

    def _alter_vocable_entry(self, vocable_entry: VocableEntry) -> int:
        """ Returns:
                n_printed_lines: int """

        old_line_repr = vocable_entry.line_repr
        KeyboardController().type(f'{old_line_repr}')
        new_entry_components = input('').split(' - ')

        if len(new_entry_components) != 2:
            print('Invalid alteration')
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
    def _plot_training_history(self):
        plt.style.use('dark_background')

        training_history = self._backend.mongodb_client.query_training_chronic()
        trained_sentences, trained_vocabulary = map(lambda abb: [date_dict[abb] if date_dict.get(abb) is not None else 0 for date_dict in training_history.values()], ['s', 'v'])

        # omit year, invert day & month for proper tick label display
        dates = ['-'.join(date.split('-')[1:][::-1]) for date in training_history.keys()]

        fig, ax = plt.subplots()
        fig.canvas.draw()
        fig.canvas.set_window_title("Way to go!")

        x_range = np.arange(len(dates))
        ax.plot(x_range, trained_sentences, marker='.', markevery=list(x_range), color='r', label='sentences')
        ax.plot(x_range, trained_vocabulary, marker='.', markevery=list(x_range), color='y', label='vocable entries')
        ax.set_xticks(x_range)
        ax.set_xticklabels(dates, minor=False, rotation=45)
        ax.set_title(f'{self._backend.language} Training History')
        ax.set_ylabel('n faced items')
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.legend(loc='upper left')
        center_matplotlib_windows()
        plt.show()

    # -----------------
    # Dunder(s)
    # -----------------
    def __str__(self):
        return self.__class__.__name__[0].lower()
