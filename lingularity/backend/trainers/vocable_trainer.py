from typing import List, Dict, Optional, Any, Iterator
from collections import Counter
from itertools import repeat, starmap

import unidecode
import numpy as np

from lingularity.backend.trainers.base import TrainerBackend
from lingularity.backend.database import MongoDBClient
from lingularity.backend.utils.enum import ExtendedEnum
from lingularity.frontend.console.utils.date import n_days_ago


class VocableEntry:
    """ wrapper for vocable vocable_entry dictionary of structure
            {foreign_token: {tf: int},
                            {lfd: Optional[str]},
                            {s: float},
                            {t: str}}

        returned by mongodb, facilitating access to attributes, as well as
        providing additional convenience functionality """

    RawType = Dict[str, Dict[str, Any]]

    @classmethod
    def new(cls, vocable: str, translation: str):
        return cls({vocable: {'tf': 0,
                              'lfd': None,
                              's': 0,
                              't': translation}}, None)

    def __init__(self, entry: RawType, reference_to_foreign: Optional[bool]):
        self.entry = entry
        self._reference_to_foreign = reference_to_foreign

    def alter(self, new_vocable: str, new_translation: str):
        self.entry[self.token]['t'] = new_translation
        self.entry[new_vocable] = self.entry.pop(self.token)

    # -----------------
    # Token
    # -----------------
    @property
    def token(self) -> str:
        return next(iter(self.entry.keys()))

    @property
    def display_token(self) -> str:
        return self.translation if not self._reference_to_foreign else self.token

    # -----------------
    # Translation
    # -----------------
    @property
    def translation(self) -> str:
        return self.entry[self.token]['t']

    @property
    def display_translation(self) -> str:
        return self.translation if self._reference_to_foreign else self.token

    # -----------------
    # Additional properties
    # -----------------
    @property
    def last_faced_date(self) -> Optional[str]:
        return self.entry[self.token]['lfd']

    @property
    def score(self) -> float:
        return self.entry[self.token]['s']

    @score.setter
    def score(self, value):
        self.entry[self.token]['s'] = value

    def update_score(self, increment: float):
        self.score += increment

    @property
    def is_new(self) -> bool:
        return self.last_faced_date is None

    @property
    def line_repr(self) -> str:
        """ i.e. f'{token} - {translation}' """

        return ' - '.join([self.token, self.translation])

    @property
    def is_perfected(self) -> bool:
        if self.last_faced_date is None:
            return False
        else:
            return self.score >= 5 and n_days_ago(self.last_faced_date) < 50

    # -----------------
    # Dunder(s)
    # -----------------
    def __str__(self):
        return str(self.entry)


class VocableTrainerBackend(TrainerBackend):
    def __init__(self, non_english_language: str, train_english: bool, mongodb_client: MongoDBClient):
        super().__init__(non_english_language, train_english, mongodb_client)

        self._sentence_data, self.lets_go_translation = self._process_sentence_data_file()
        self._token_2_sentence_indices = self._get_token_map(self._sentence_data)
        self._vocable_entries: Optional[List[VocableEntry]] = None

    def set_item_iterator(self) -> Iterator[Any]:
        self._vocable_entries = self._get_imperfect_vocable_entries()
        self.n_training_items = len(self._vocable_entries)
        self._item_iterator: Iterator[VocableEntry] = self._get_item_iterator(self._vocable_entries)

    def _get_imperfect_vocable_entries(self) -> List[VocableEntry]:
        entire_vocabulary = starmap(VocableEntry, zip(self.mongodb_client.query_vocabulary_data(), repeat(self._train_english)))
        return list(filter(lambda vocable_entry: not vocable_entry.is_perfected, entire_vocabulary))

    # ---------------
    # Pre training
    # ---------------
    def get_new_vocable_entries(self) -> List[VocableEntry]:
        return list(filter(lambda entry: entry.is_new, self._vocable_entries))

    # ---------------
    # Training
    # ---------------

    # ---------------
    # .Evaluation
    # ---------------
    class ResponseEvaluation(ExtendedEnum):
        Wrong = 0.0
        AlmostCorrect = 0.5
        AccentError = 0.75
        Perfect = 1.0

    def get_response_evaluation(self, response: str, translation: str) -> ResponseEvaluation:
        distinct_translations = translation.split(',')
        accent_pruned_translations = list(map(unidecode.unidecode, distinct_translations))

        def tolerable_error():
            def n_deviations(a: str, b: str) -> int:
                def dict_value_sum(dictionary):
                    return sum(list(dictionary.values()))
                short, long = sorted([a, b], key=lambda string: len(string))
                short_c, long_c = map(Counter, [short, long])  # type: ignore
                return dict_value_sum(long_c - short_c)

            TOLERATED_CHAR_DEVIATIONS = 1
            return any(n_deviations(response, translation) <= TOLERATED_CHAR_DEVIATIONS for translation in distinct_translations)

        if response in translation.split(','):
            return self.ResponseEvaluation.Perfect
        elif response in accent_pruned_translations:
            return self.ResponseEvaluation.AccentError
        elif tolerable_error():
            return self.ResponseEvaluation.AlmostCorrect
        else:
            return self.ResponseEvaluation.Wrong

    # ------------------
    # .related sentences
    # ------------------
    def get_related_sentence_pairs(self, entry: str, n: int) -> Optional[List[List[str]]]:
        if (sentence_indices := self._token_2_sentence_indices.query_sentence_indices(entry)) is None:
            return None

        sentence_indices = np.asarray(sentence_indices)
        np.random.shuffle(sentence_indices)
        return self._sentence_data[sentence_indices[:n]]  # type: ignore
