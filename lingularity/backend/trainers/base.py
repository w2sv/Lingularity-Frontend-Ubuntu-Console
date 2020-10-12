from typing import List, Optional, Iterator, Any, Sequence
import os
from abc import ABC, abstractmethod

import numpy as np

from lingularity.backend import BASE_LANGUAGE_DATA_PATH
from lingularity.backend.database import MongoDBClient
from lingularity.backend.trainers.components.forename_conversion import ForenameConvertor
from lingularity.backend.trainers.components.sentence_data import SentenceData
from lingularity.backend.trainers.components.tts import TTS


class TrainerBackend(ABC):
    def __init__(self, non_english_language: str, train_english: bool, mongodb_client: MongoDBClient):
        if not os.path.exists(BASE_LANGUAGE_DATA_PATH):
            os.mkdir(BASE_LANGUAGE_DATA_PATH)

        self._non_english_language = non_english_language
        self._train_english = train_english

        mongodb_client.language = non_english_language
        self.mongodb_client = mongodb_client

        self._item_iterator: Iterator[Any]
        self.n_training_items: int

        self.forename_converter = ForenameConvertor(self.language, train_english=train_english)
        self.tts = TTS(self.language, mongodb_client)

    @property
    def locally_available_languages(self) -> List[str]:
        return os.listdir(BASE_LANGUAGE_DATA_PATH)

    @property
    def language(self):
        return self._non_english_language if not self._train_english else 'English'

    @staticmethod
    @abstractmethod
    def get_eligible_languages(mongodb_client: Optional[MongoDBClient]) -> List[str]:
        pass

    # ----------------
    # Paths
    # ----------------
    @property
    def _language_dir_path(self):
        return f'{BASE_LANGUAGE_DATA_PATH}/{self.language}'

    # ----------------
    # Pre Training
    # ----------------
    @abstractmethod
    def set_item_iterator(self):
        """ Sets item iterator, n training items """
        pass

    def _set_item_iterator(self, training_items: Sequence[Any]):
        self.n_training_items = len(training_items)
        self._item_iterator = self._get_item_iterator(training_items)

    def _get_sentence_data(self) -> SentenceData:
        return SentenceData(self._non_english_language, self._train_english)

    @staticmethod
    def _get_item_iterator(item_list: Sequence[Any]) -> Iterator[Any]:
        np.random.shuffle(item_list)
        return iter(item_list)

    # -----------------
    # Training
    # -----------------
    def get_training_item(self) -> Optional[Any]:
        """
            Returns:
                 None in case of depleted iterator """

        assert self._item_iterator is not None

        try:
            return next(self._item_iterator)
        except StopIteration:
            return None

    # -----------------
    # Post training
    # -----------------
    def enter_session_statistics_into_database(self, n_trained_items: int):
        update_args = (self.__str__(), n_trained_items)

        self.mongodb_client.update_last_session_statistics(*update_args)
        self.mongodb_client.inject_session_statistics(*update_args)

    # -----------------
    # Dunder(s)
    # -----------------
    def __str__(self):
        return self.__class__.__name__[0].lower()


if __name__ == '__main__':
    s = SentenceData('French')
    print(s.foreign_language_sentences.uses_latin_script)
    print(s.foreign_language_sentences.uses_latin_script)
