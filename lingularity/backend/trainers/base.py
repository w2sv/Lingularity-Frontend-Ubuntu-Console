from typing import List, Optional, Iterator, Any, Sequence, Tuple
import os
from abc import ABC
from functools import cached_property

import nltk
import numpy as np

from lingularity.database import MongoDBClient


class TrainerBackend(ABC):
    BASE_LANGUAGE_DATA_PATH = f'{os.getcwd()}/language_data'

    DEFAULT_NAMES = ('Tom', 'Mary')
    LANGUAGE_CORRESPONDING_NAMES = {
        'Italian': ('Alessandro', 'Christina'),
        'French': ('Antoine', 'Amelie'),
        'Spanish': ('Emilio', 'Luciana'),
        'Hungarian': ('László', 'Zsóka'),
        'German': ('Günther', 'Irmgard')
    }

    def __init__(self, non_english_language: str, train_english: bool, mongodb_client: MongoDBClient):
        if not os.path.exists(self.BASE_LANGUAGE_DATA_PATH):
            os.mkdir(self.BASE_LANGUAGE_DATA_PATH)

        self._non_english_language = non_english_language
        self._train_english = train_english
        self.names_convertible = self.LANGUAGE_CORRESPONDING_NAMES.get(self._non_english_language) is not None

        mongodb_client.language = non_english_language
        self.mongodb_client = mongodb_client

        self._item_iterator: Optional[Iterator[Any]] = None
        self.lets_go_translation: Optional[str] = None

    @staticmethod
    def _get_item_iterator(item_list: Sequence[Any]) -> Iterator[Any]:
        np.random.shuffle(item_list)
        return iter(item_list)

    @property
    def locally_available_languages(self) -> List[str]:
        return os.listdir(self.BASE_LANGUAGE_DATA_PATH)

    def adopt_database_client(self, client: MongoDBClient):
        client.language = self._non_english_language
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

    @cached_property
    def stemmer(self) -> Optional[nltk.stem.SnowballStemmer]:
        assert self.language is not None, 'Stemmer to be initially called after language setting'

        if (lowered_language := self.language.lower()) in nltk.stem.SnowballStemmer.languages:
            return nltk.stem.SnowballStemmer(lowered_language)
        else:
            return None

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
    def _process_sentence_data_file(self) -> Tuple[np.ndarray, Optional[str]]:
        sentence_data = self._parse_sentence_data()
        return sentence_data, self._query_lets_go_translation(sentence_data)

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

    @staticmethod
    def _query_lets_go_translation(unshuffled_sentence_data: np.ndarray) -> Optional[str]:
        for content, i in ((sentence_pair[0], i) for i, sentence_pair in
                                    enumerate(unshuffled_sentence_data[:int(len(unshuffled_sentence_data) * 0.3)])):
            if content == "Let's go!":
                return unshuffled_sentence_data[i][1]
        return None

    def get_training_item(self) -> Optional[Any]:
        """
            Returns:
                 None in case of depleted iterator """

        assert self._item_iterator is not None

        try:
            return next(self._item_iterator)
        except StopIteration:
            return None

    def accommodate_names(self, sentence: str) -> str:
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
        assert self.mongodb_client is not None

        update_args = (str(self), n_trained_items)

        self.mongodb_client.update_last_session_statistics(*update_args)
        self.mongodb_client.inject_session_statistics(*update_args)
