from typing import List, Dict, Optional, Any, Iterator
from collections import Counter
from itertools import repeat, starmap

import unidecode
import numpy as np

from lingularity.backend.trainers.base import TrainerBackend
from lingularity.database import MongoDBClient
from lingularity.backend.types.token_maps import RawToken2SentenceIndices
from lingularity.utils.strings import get_article_stripped_token
from lingularity.utils.enum import ExtendedEnum


class VocableEntry:
    """ wrapper for vocable entry dictionary of structure
            {foreign_token: {tf: int},
                            {lfd: str},
                            {s: float},
                            {t: str}}

        returned by mongodb, facilitating access to attributes, as well as
        providing additional convenience functionality """

    RawType = Dict[str, Dict[str, Any]]

    def __init__(self, entry: RawType, reference_to_foreign: bool):
        self._entry = entry
        self._reference_to_foreign = reference_to_foreign

    # -----------------
    # Token
    # -----------------
    @property
    def token(self) -> str:
        return next(iter(self._entry.keys()))

    @property
    def display_token(self) -> str:
        return self.translation if not self._reference_to_foreign else self.token

    # -----------------
    # Translation
    # -----------------
    @property
    def translation(self) -> str:
        return self._entry[self.token]['t']

    @property
    def display_translation(self) -> str:
        return self.translation if self._reference_to_foreign else self.token

    # -----------------
    # Additional properties
    # -----------------
    @property
    def last_faced_date(self) -> Optional[str]:
        return self._entry[self.token]['lfd']

    @property
    def is_new(self) -> bool:
        return self.last_faced_date is None

    @property
    def line_repr(self) -> str:
        """ i.e. f'{token} - {translation}' """

        return ' - '.join([self.token, self.translation])

    # -----------------
    # Dunder(s)
    # -----------------
    def __str__(self):
        return str(self._entry)


class VocableTrainerBackend(TrainerBackend):
    def __init__(self, non_english_language: str, train_english: bool, mongodb_client: MongoDBClient):
        super().__init__(non_english_language, train_english, mongodb_client)

        self._sentence_data, self.lets_go_translation = self._process_sentence_data_file()

        self._token_2_rowinds = RawToken2SentenceIndices(self._sentence_data, language=self.language)
        self._vocable_entries: List[VocableEntry] = self._get_vocable_entries()

        self._item_iterator: Iterator[VocableEntry] = self._get_item_iterator(self._vocable_entries)

    # ---------------
    # Initialization
    # ---------------
    def _get_vocable_entries(self) -> List[VocableEntry]:
        return list(starmap(VocableEntry, zip(self.mongodb_client.query_vocabulary_data(), repeat(self._train_english))))

    @property
    def n_imperfect_vocable_entries(self) -> int:
        return len(self._vocable_entries)

    def get_new_vocable_entries(self) -> List[VocableEntry]:
        return list(filter(lambda entry: entry.is_new, self._vocable_entries))

    # ---------------
    # Evaluation
    # ---------------
    class ResponseEvaluation(ExtendedEnum):
        Wrong = 0
        AccentError = 0.5
        AlmostCorrect = 0.5
        Perfect = 1

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
    # Sentence Query
    # ------------------
    def get_related_sentences(self, token: str, n: int) -> Optional[List[str]]:
        WORD_ROOT_LENGTH = 4

        root = get_article_stripped_token(token)[:WORD_ROOT_LENGTH]
        sentence_indices = np.asarray(self._token_2_rowinds.get_root_comprising_sentence_indices(root))
        if not len(sentence_indices):
            return None

        random_indices = np.random.randint(0, len(sentence_indices), n)
        return self._sentence_data[sentence_indices[random_indices]][:, 1]
