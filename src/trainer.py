from abc import ABC, abstractmethod
from typing import Callable, Optional, List, Dict
import os
import platform
import sys
import time

from tqdm import tqdm
import numpy as np


TokenSentenceindsMap = Dict[str, List[int]]


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
        print("Couldn't resolve input")
        time.sleep(1)
        Trainer.clear_screen()
        return func()

    @staticmethod
    def resolve_input(input: str, options: List[str]) -> Optional[str]:
        options_starting_with = [o for o in options if o.startswith(input)]
        if len(options_starting_with) == 1:
            return options_starting_with[0]
        else:
            return None

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

        if self.reference_language_inversion:
            split_data = [list(reversed(row)) for row in split_data]

        return np.array(split_data)

    def procure_token_2_rowinds_map(self) -> TokenSentenceindsMap:
        token_2_rowinds = {}
        print('Parsing data...')
        for i, sentence in enumerate(tqdm(self.sentence_data[:, 1])):
            for token in sentence.split(' '):
                if token_2_rowinds.get(token) is None:
                    token_2_rowinds[token] = [i]
                else:
                    token_2_rowinds[token].append(i)
        return token_2_rowinds

    def get_lets_go_translation(self) -> Optional[str]:
        lets_go_occurrence_range = ((sentence_pair[0], i) for i, sentence_pair in
                                    enumerate(self.sentence_data[:int(len(self.sentence_data) * 0.3)]))
        for content, i in lets_go_occurrence_range:
            if content == "Let's go!":
                return self.sentence_data[i][1]
        return None

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
