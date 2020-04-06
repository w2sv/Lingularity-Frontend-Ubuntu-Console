from abc import ABC, abstractmethod
from typing import Callable
import os
import platform
import sys
import time

import numpy as np


class Trainer(ABC):
    def __init__(self):
        self.base_data_path = os.path.join(os.getcwd(), 'language_data')
        self._language = None  # equals reference language in case of reference language inversion
        self.reference_language_inversion = False

        self.sentence_data = None

    @property
    def language(self):
        return self._language if not self.reference_language_inversion else 'English'

    @language.setter
    def language(self, value):
        self._language = value

    @property
    def sentence_file_path(self):
        return f'{self.base_data_path}/{self._language}/sentence_data.txt'

    @property
    def vocabulary_file_path(self):
        return f'{self.base_data_path}/{self.language}/vocabulary.txt'

    @staticmethod
    def clear_screen():
        os.system('cls' if platform.system() == 'Windows' else 'clear')

    @staticmethod
    def erase_previous_line():
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K")

    @staticmethod
    def recurse_on_invalid_input(func: Callable):
        print('Invalid input')
        time.sleep(1)
        Trainer.clear_screen()
        return func()

    def parse_sentence_data(self) -> np.ndarray:
        data = open(self.sentence_file_path, 'r', encoding='utf-8').readlines()
        split_data = [i.split('\t') for i in data]

        # remove reference appendices from source file if still present
        if len(split_data[0]) > 2:
            bilateral_sentences = ('\t'.join(row_splits[:2]) + '\n' for row_splits in split_data)
            with open(self.sentence_file_path, 'w', encoding='utf-8') as write_file:
                write_file.writelines(bilateral_sentences)

        for i, row in enumerate(split_data):
            split_data[i][1] = row[1].strip('\n')

        if self.reference_language_inversion:
            split_data = [list(reversed(row)) for row in split_data]

        return np.array(split_data)

    @abstractmethod
    def select_language(self):
        pass

    @abstractmethod
    def train(self):
        pass

    @abstractmethod
    def run(self):
        pass
