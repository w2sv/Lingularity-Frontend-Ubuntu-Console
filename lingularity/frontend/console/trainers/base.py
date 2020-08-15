from typing import Optional, Tuple
from abc import ABC, abstractmethod
import time

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from lingularity.backend.trainers import TrainerBackend
from lingularity.utils.output_manipulation import BufferPrint, centered_print
from lingularity.utils.input_resolution import resolve_input
from lingularity.utils.matplotlib import center_matplotlib_windows


class TrainerConsoleFrontend(ABC):
    plt.rcParams['toolbar'] = 'None'
    SELECTION_QUERY_OUTPUT_OFFSET = '\n\t'

    def __init__(self):
        self._backend: Optional[TrainerBackend] = None
        self._n_trained_items: int = 0

        self._buffer_print = BufferPrint()

    # -----------------
    # Driver
    # -----------------
    @abstractmethod
    def run(self):
        pass

    # -----------------
    # Pre Training
    # -----------------
    @abstractmethod
    def _select_language(self) -> Tuple[str, bool]:
        pass

    @abstractmethod
    def _display_pre_training_instructions(self):
        pass

    def _output_lets_go(self):
        if self._backend.lets_go_translation is not None:
            output = self._backend.lets_go_translation
        else:
            output = "Let's go!"
        centered_print(output, '\n' * 2)

    # -----------------
    # Training
    # -----------------
    @abstractmethod
    def _run_training(self):
        pass

    def insert_vocable_into_database(self) -> Tuple[Optional[str], int]:
        """ Returns:
                inserted vocable entry line repr, None in case of invalid input
                number of printed lines """

        assert self._backend is not None
        vocable = input(f'Enter {self._backend.language} word/phrase: ')

        if resolve_input(vocable, ['#exit']) == '#exit':
            raise SystemExit

        meanings = input('Enter meaning(s): ')

        if not all([vocable, meanings]):
            print("Input field left unfilled")
            time.sleep(1)
            return None, 3

        self._backend.mongodb_client.insert_vocable(vocable, meanings)
        return ' - '.join([vocable, meanings]), 2

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
