from typing import Optional, Iterator, Any, Sequence
from abc import ABC, abstractmethod

import numpy as np

from lingularity.backend.database import MongoDBClient
from lingularity.backend.components import ForenameConvertor, SentenceData
from lingularity.utils import string_resources as string_resources


class TrainerBackend(ABC):
    def __init__(self, non_english_language: str, train_english: bool):
        self._non_english_language = non_english_language
        self._train_english = train_english

        self.mongodb_client = MongoDBClient.get_instance()
        self.mongodb_client.language = self.language

        self._item_iterator: Iterator[Any]
        self.n_training_items: int

        self.forename_converter: Optional[ForenameConvertor] = self._get_forename_converter()

    @property
    def language(self) -> str:
        return [self._non_english_language, string_resources.ENGLISH][self._train_english]

    # ----------------
    # Forename Conversion
    # ----------------
    def _get_forename_converter(self) -> Optional[ForenameConvertor]:
        if ForenameConvertor.available_for(self._non_english_language):
            return ForenameConvertor(self._non_english_language, train_english=self._train_english)
        return None

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

    @staticmethod
    def _get_item_iterator(item_list: Sequence[Any]) -> Iterator[Any]:
        np.random.shuffle(item_list)
        return iter(item_list)

    def _get_sentence_data(self) -> SentenceData:
        return SentenceData(self._non_english_language, self._train_english)

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
    # Post Training
    # -----------------
    def enter_session_statistics_into_database(self, n_trained_items: int):
        update_args = (str(self), n_trained_items)

        self.mongodb_client.update_last_session_statistics(*update_args)
        self.mongodb_client.inject_session_statistics(*update_args)

    # -----------------
    # Dunder(s)
    # -----------------
    def __str__(self):
        return self.__class__.__name__[0].lower()
