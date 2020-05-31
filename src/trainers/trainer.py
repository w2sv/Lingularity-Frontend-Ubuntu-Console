from abc import ABC, abstractmethod
from typing import Callable, Optional, Iterable, Dict
import os
import platform
import sys
import time
import json
import datetime
from functools import lru_cache

import nltk
import numpy as np
import matplotlib.pyplot as plt


class Trainer(ABC):
    BASE_DATA_PATH = os.path.join(os.getcwd(), 'language_data')

    def __init__(self):
        if not os.path.exists(self.BASE_DATA_PATH):
            os.mkdir(self.BASE_DATA_PATH)
        self._language = None  # equals reference language in case of english training
        self._train_english = False

        self.sentence_data = None

        plt.rcParams['toolbar'] = 'None'

        self.n_trained_items = 0

    @property
    def train_english(self):
        return self._train_english

    @train_english.setter
    def train_english(self, flag: bool):
        """ create english dir if necessary """
        if flag is True and not os.path.exists(self.language_dir):
            os.mkdir(self.language_dir)
        self._train_english = flag

    @property
    def language(self):
        return self._language if not self._train_english else 'English'

    @language.setter
    def language(self, value: str):
        self._language = value

    @property
    @lru_cache()
    def stemmer(self) -> Optional[nltk.stem.SnowballStemmer]:
        assert self.language is not None, 'stemmer to be initially called after language setting'
        lowered_language = self.language.lower()
        return None if lowered_language not in nltk.stem.SnowballStemmer.languages else nltk.stem.SnowballStemmer(lowered_language)

    @property
    def language_dir(self):
        return f'{self.BASE_DATA_PATH}/{self.language}'

    def _language_dir_sub_path(self, sub_path: str) -> str:
        return f'{self.language_dir}/{sub_path}'

    @property
    def sentence_file_path(self):
        return self._language_dir_sub_path('sentence_data.txt')

    @property
    def vocabulary_file_path(self):
        return self._language_dir_sub_path('vocabulary.txt')

    @property
    def training_documentation_file_path(self):
        return self._language_dir_sub_path('training_documentation.json')

    @property
    def today(self) -> str:
        return str(datetime.date.today())

    # ------------------
    # STATICS
    # ------------------
    @staticmethod
    def clear_screen():
        os.system('cls' if platform.system() == 'Windows' else 'clear')

    @staticmethod
    def erase_previous_line():
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K")

    @staticmethod
    def recurse_on_invalid_input(func: Callable):
        print("Couldn't resolve input")
        time.sleep(1)
        Trainer.clear_screen()
        return func()

    @staticmethod
    def resolve_input(input: str, options: Iterable[str]) -> Optional[str]:
        options_starting_with = [o for o in options if o.startswith(input)]
        return options_starting_with[0] if len(options_starting_with) == 1 else None

    # ----------------
    # METHODS
    # ----------------
    def load_training_history(self) -> Dict[str, Dict[str, int]]:
        if not os.path.exists(self.training_documentation_file_path):
            return {}
        with open(self.training_documentation_file_path, 'r') as load_file:
            return json.load(load_file)

    def parse_sentence_data(self) -> np.ndarray:
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
        # split_data = (row[0], row[1].strip('\n') for row in split_data)

        if self._train_english:
            split_data = [list(reversed(row)) for row in split_data]

        return np.asarray(split_data)

    def get_lets_go_translation(self) -> Optional[str]:
        lets_go_occurrence_range = ((sentence_pair[0], i) for i, sentence_pair in
                                    enumerate(self.sentence_data[:int(len(self.sentence_data) * 0.3)]))
        for content, i in lets_go_occurrence_range:
            if content == "Let's go!":
                return self.sentence_data[i][1]
        return None

    def append_2_training_history(self):
        training_history = self.load_training_history()
        trainer_abbreviation = self.__class__.__name__[0].lower()
        if training_history.get(self.today) is not None and training_history[self.today].get(trainer_abbreviation) is not None:
            training_history[self.today][trainer_abbreviation] += self.n_trained_items
        elif training_history.get(self.today) is not None:
            training_history[self.today][trainer_abbreviation] = self.n_trained_items
        else:
            training_history[self.today] = {trainer_abbreviation: self.n_trained_items}

        with open(self.training_documentation_file_path, 'w+') as write_file:
            json.dump(training_history, write_file)

    def plot_training_history(self):
        plt.style.use('dark_background')

        training_history = self.load_training_history()
        trained_sentences, trained_vocabulary = map(lambda abb: [date_dict[abb] if date_dict.get(abb) is not None else 0 for date_dict in training_history.values()], ['s', 'v'])

        # ommitting year, inverting day & month for proper tick label display
        dates = ['-'.join(date.split('-')[1:][::-1]) for date in training_history.keys()]

        fig, ax = plt.subplots()
        fig.canvas.draw()
        fig.canvas.set_window_title("Way to go!")

        x_range = np.arange(len(dates))
        ax.plot(x_range, trained_sentences, marker='.', markevery=list(x_range), color='r', label='sentences')
        ax.plot(x_range, trained_vocabulary, marker='.', markevery=list(x_range), color='b', label='vocabulary')
        ax.set_xticks(x_range)
        ax.set_xticklabels(dates, minor=False, rotation=45)
        ax.set_title(f'{self.language} training history')
        ax.set_ylabel('n faced items')
        ax.set_ylim(bottom=0)
        ax.legend(loc='upper left')
        plt.show()

    # -----------------
    # ABSTRACTS
    # -----------------
    @abstractmethod
    def pre_training_display(self):
        pass

    @abstractmethod
    def select_language(self):
        pass

    @abstractmethod
    def train(self):
        pass

    @abstractmethod
    def run(self):
        pass
