from typing import List, Optional
import os
from abc import ABC, abstractmethod
from functools import cached_property

import nltk
import numpy as np

from lingularity.database import MongoDBClient


class TrainerBackend(ABC):
    BASE_LANGUAGE_DATA_PATH = os.path.join(os.getcwd(), 'language_data')

    DEFAULT_NAMES = ('Tom', 'Mary')
    LANGUAGE_CORRESPONDING_NAMES = {
        'Italian': ('Alessandro', 'Christina'),
        'French': ('Antoine', 'Amelie'),
        'Spanish': ('Emilio', 'Luciana'),
        'Hungarian': ('László', 'Zsóka'),
        'German': ('Günther', 'Irmgard')
    }

    def __init__(self, non_english_language: str, train_english: bool):
        if not os.path.exists(self.BASE_LANGUAGE_DATA_PATH):
            os.mkdir(self.BASE_LANGUAGE_DATA_PATH)

        self._non_english_language = non_english_language
        self._train_english = train_english
        self._names_convertible = self.LANGUAGE_CORRESPONDING_NAMES.get(self._non_english_language) is not None

        self.mongodb_client: Optional[MongoDBClient] = None
        self._sentence_data: np.ndarray = None

    @property
    def locally_available_languages(self) -> List[str]:
        return os.listdir(self.BASE_LANGUAGE_DATA_PATH)

    def adopt_database_client(self, client: MongoDBClient):
        client.set_language(self._non_english_language)
        self.mongodb_client = client

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

    def query_lets_go_translation(self) -> Optional[str]:
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
    def insert_session_statistics_into_database(self, n_trained_items: int):
        update_args = (str(self), n_trained_items)

        self.mongodb_client.update_last_session_statistics(*update_args)
        self.mongodb_client.inject_session_statistics(*update_args)

    # -----------------
    # Dunders
    # -----------------
    def __str__(self):
        return self.__class__.__name__[0].lower()
