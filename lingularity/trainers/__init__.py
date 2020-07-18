import json
import os
from abc import ABC, abstractmethod
from functools import cached_property
from typing import List, Optional, Dict

import nltk
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from lingularity.utils.datetime import datetag_today
from lingularity import database


class Trainer(ABC):
    BASE_LANGUAGE_DATA_PATH = os.path.join(os.getcwd(), 'language_data')
    plt.rcParams['toolbar'] = 'None'

    def __init__(self):
        if not os.path.exists(self.BASE_LANGUAGE_DATA_PATH):
            os.mkdir(self.BASE_LANGUAGE_DATA_PATH)

        self._non_english_language: str = self._select_language()  # equals reference language in case of english training
        self._train_english: bool = False
        self._sentence_data: np.ndarray = None
        self._n_trained_items: int = 0

        self._today = datetag_today()

        self._database_client = database.MongoDBClient('janek_zangenberg', self._non_english_language,
                                                       database.Credentials.default())

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

    # ----------------
    # .Sub
    # ----------------
    def _language_dir_sub_path(self, sub_path: str) -> str:
        return f'{self.language_dir_path}/{sub_path}'

    @property
    def sentence_file_path(self):
        return self._language_dir_sub_path('sentence_data.txt')

    @property
    def vocabulary_file_path(self):
        return self._language_dir_sub_path('vocabulary.txt')

    @property
    def training_documentation_file_path(self):
        return self._language_dir_sub_path('training_documentation.json')

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

    # -----------------
    # .Training History
    # -----------------
    def _load_training_history(self) -> Optional[Dict[str, Dict[str, int]]]:
        try:
            with open(self.training_documentation_file_path, 'r') as load_file:
                return json.load(load_file)
        except FileNotFoundError:
            return None

    def _append_session_statistics_to_training_history(self):
        training_history = self._load_training_history()
        if not training_history:
            training_history = {}

        if training_history.get(self._today) is not None and training_history[self._today].get(str(self)) is not None:
            training_history[self._today][str(self)] += self._n_trained_items

        elif training_history.get(self._today) is not None:
            training_history[self._today][str(self)] = self._n_trained_items
        else:
            training_history[self._today] = {str(self): self._n_trained_items}

        with open(self.training_documentation_file_path, 'w+') as write_file:
            json.dump(training_history, write_file)

    def _insert_session_statistics_into_database(self):
        self._database_client.inject_session_statistics(str(self), self._n_trained_items)

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
        ax.plot(x_range, trained_vocabulary, marker='.', markevery=list(x_range), color='b', label='_vocabulary')
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
