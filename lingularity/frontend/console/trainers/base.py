from typing import Optional, Tuple, Type
from abc import ABC, abstractmethod
import time

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from lingularity.backend.trainers import TrainerBackend
from lingularity.database import MongoDBClient
from lingularity.utils.output_manipulation import BufferPrint


class TrainerConsoleFrontend(ABC):
    plt.rcParams['toolbar'] = 'None'
    SELECTION_QUERY_OFFSET = '\n\t'

    def __init__(self):
        self._backend: Optional[TrainerBackend] = None
        self._n_trained_items: int = 0

        self._buffer_print = BufferPrint()

    def relay_database_client_to_backend(self, client: MongoDBClient):
        assert self._backend is not None, 'backend not initialized'

        self._backend.adopt_database_client(client)

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def _select_language(self) -> Tuple[str, bool]:
        pass

    @abstractmethod
    def _run_training(self):
        pass

    @abstractmethod
    def _display_pre_training_instructions(self):
        pass

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
        ax.plot(x_range, trained_vocabulary, marker='.', markevery=list(x_range), color='b', label='vocable entries')
        ax.set_xticks(x_range)
        ax.set_xticklabels(dates, minor=False, rotation=45)
        ax.set_title(f'{self._backend.language} training history')
        ax.set_ylabel('n faced items')
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.legend(loc='upper left')
        plt.show()

    # -----------------
    # .Database related
    # -----------------
    def _insert_vocable_into_database(self) -> Tuple[Optional[str], int]:
        """ Returns:
                inserted vocable entry, None in case of invalid input
                 number of printed lines """

        assert self._backend is not None and self._backend.mongodb_client is not None
        vocable = input(f'Enter {self._backend.language} word/phrase: ')
        meanings = input('Enter meaning(s): ')

        if not all([vocable, meanings]):
            print("Input field left unfilled")
            time.sleep(1)
            return None, 3

        self._backend.mongodb_client.insert_vocable(vocable, meanings)
        return ' - '.join([vocable, meanings]), 2

    # -----------------
    # Dunders
    # -----------------
    def __str__(self):
        return self.__class__.__name__[0].lower()
