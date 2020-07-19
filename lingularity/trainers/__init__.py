from typing import List, Optional, Tuple
import os
from abc import ABC, abstractmethod
from functools import cached_property
import time

import nltk
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from lingularity.database import MongoDBClient
from lingularity.utils.output_manipulation import BufferPrint


class Trainer(ABC):
    BASE_LANGUAGE_DATA_PATH = os.path.join(os.getcwd(), 'language_data')
    plt.rcParams['toolbar'] = 'None'

    DEFAULT_NAMES = ('Tom', 'Mary')
    LANGUAGE_CORRESPONDING_NAMES = {
        'Italian': ('Alessandro', 'Christina'),
        'French': ('Antoine', 'Amelie'),
        'Spanish': ('Emilio', 'Luciana'),
        'Hungarian': ('László', 'Zsóka'),
        'German': ('Günther', 'Irmgard')
    }

    def __init__(self, database_client: MongoDBClient):
        if not os.path.exists(self.BASE_LANGUAGE_DATA_PATH):
            os.mkdir(self.BASE_LANGUAGE_DATA_PATH)

        self._database_client = database_client
        self._non_english_language: str = self._select_language()
        self._train_english: bool = False
        self._sentence_data: np.ndarray = None
        self._n_trained_items: int = 0

        self._names_convertible = self.LANGUAGE_CORRESPONDING_NAMES.get(self._non_english_language) is not None

        self._database_client.set_language(self._non_english_language)

        self._buffer_print = BufferPrint()

    @abstractmethod
    def _select_language(self) -> str:
        # TODO: make return language, train_english
        pass

    @property
    def locally_available_languages(self) -> List[str]:
        return os.listdir(self.BASE_LANGUAGE_DATA_PATH)

    @property
    def train_english(self):
        return self._train_english

    @train_english.setter
    def train_english(self, flag: bool):
        """ creates english dir if necessary """

        assert self._train_english is False, 'train_english not to be changed after being set to True'

        if flag is True and not os.path.exists(self.language_dir_path):
            os.mkdir(self.language_dir_path)
        self._train_english = flag

    @property
    def language(self):
        return self._non_english_language if not self._train_english else 'English'

    @cached_property  # TODO: ascertain proper working
    def stemmer(self) -> Optional[nltk.stem.SnowballStemmer]:
        assert self.language is not None, 'Stemmer to be initially called after language setting'
        lowered_language = self.language.lower()
        return None if lowered_language not in nltk.stem.SnowballStemmer.languages else nltk.stem.SnowballStemmer(lowered_language)

    # ----------------
    # Paths
    # ----------------
    @property
    def language_dir_path(self):
        return f'{self.BASE_LANGUAGE_DATA_PATH}/{self.language}'

    @property
    def sentence_file_path(self) -> str:
        return f'{self.language_dir_path}/sentence_data.txt'

    # ----------------
    # Methods
    # ----------------
    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def _train(self):
        pass

    @abstractmethod
    def _display_pre_training_instructions(self):
        pass

    def _parse_sentence_data(self) -> np.ndarray:
        data = open(self.sentence_file_path, 'r', encoding='utf-8').readlines()
        split_data = [i.split('\t') for i in data]

        # remove reference appendices from source file if newly downloaded
        if len(split_data[0]) > 2:
            bilingual_sentence_data = ['\t'.join(row_splits[:2]) + '\n' for row_splits in split_data]
            with open(self.sentence_file_path, 'w', encoding='utf-8') as write_file:
                write_file.writelines(bilingual_sentence_data)
            split_data = [i.split('\t') for i in bilingual_sentence_data]

        for i, row in enumerate(split_data):
            split_data[i][1] = row[1].strip('\n')

        if self._train_english:
            split_data = [list(reversed(row)) for row in split_data]

        return np.asarray(split_data)

    def _find_lets_go_translation(self) -> Optional[str]:
        lets_go_occurrence_range = ((sentence_pair[0], i) for i, sentence_pair in
                                    enumerate(self._sentence_data[:int(len(self._sentence_data) * 0.3)]))
        for content, i in lets_go_occurrence_range:
            if content == "Let's go!":
                return self._sentence_data[i][1]
        return None

    def _accommodate_names_of_sentence(self, sentence: str) -> str:
        """ Assertion of self._convertible name being True to be made before invocation """

        sentence_tokens = sentence[:-1].split(' ')
        punctuation = sentence[-1]

        for name_ind, name in enumerate(self.DEFAULT_NAMES):
            try:
                sentence_tokens[sentence_tokens.index(name)] = self.LANGUAGE_CORRESPONDING_NAMES[self.language][name_ind]
            except ValueError:
                pass
        return ' '.join(sentence_tokens) + punctuation

    # -----------------
    # .Database related
    # -----------------
    def _insert_vocable_into_database(self) -> Tuple[Optional[str], int]:
        """ Returns:
                inserted vocable entry, None in case of invalid input
                 number of printed lines """

        vocable = input(f'Enter {self.language} word/phrase: ')
        meanings = input('Enter meaning(s): ')

        if not all([vocable, meanings]):
            print("Input field left unfilled")
            time.sleep(1)
            return None, 3

        self._database_client.insert_vocable(vocable, meanings)
        return ' - '.join([vocable, meanings]), 2

    def _insert_session_statistics_into_database(self):
        update_args = (str(self), self._n_trained_items)

        self._database_client.update_last_session_statistics(*update_args)
        self._database_client.inject_session_statistics(*update_args)

    def _plot_training_history(self):
        plt.style.use('dark_background')

        training_history = self._database_client.query_training_chronic()
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
        ax.set_title(f'{self.language} training history')
        ax.set_ylabel('n faced items')
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.legend(loc='upper left')
        plt.show()

    # -----------------
    # Dunders
    # -----------------
    def __str__(self):
        return self.__class__.__name__[0].lower()
