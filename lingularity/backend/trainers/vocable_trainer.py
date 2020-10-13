from typing import List, Optional
from collections import Counter
from itertools import repeat, starmap
from enum import Enum

import unidecode
import numpy as np

from lingularity.backend.trainers.base import TrainerBackend
from lingularity.backend.database import MongoDBClient
from lingularity.backend.components import (
    SentenceData,
    VocableEntry,
    TokenMap,
    get_token_map
)


class VocableTrainerBackend(TrainerBackend):
    def __init__(self, non_english_language: str, train_english: bool, mongodb_client: MongoDBClient):
        super().__init__(non_english_language, train_english, mongodb_client)

        self._training_items: Optional[List[VocableEntry]] = None
        self._sentence_data: SentenceData = self._get_sentence_data()
        self._token_2_sentence_indices: TokenMap = get_token_map(self._sentence_data, self.language, load_normalizer=True)

    @staticmethod
    def get_eligible_languages(mongodb_client: Optional[MongoDBClient]) -> List[str]:
        assert mongodb_client is not None

        return mongodb_client.query_vocabulary_possessing_languages()

    def set_item_iterator(self):
        self._training_items = self._get_imperfect_vocable_entries()
        self._set_item_iterator(self._training_items)

    def _get_imperfect_vocable_entries(self) -> List[VocableEntry]:
        entire_vocabulary = starmap(VocableEntry, zip(self.mongodb_client.query_vocabulary_data(), repeat(self._train_english)))
        return list(filter(lambda vocable_entry: not vocable_entry.is_perfected, entire_vocabulary))

    # ---------------
    # Pre Training
    # ---------------
    def get_new_vocable_entries(self) -> List[VocableEntry]:
        assert self._training_items is not None

        return list(filter(lambda entry: entry.is_new, self._training_items))

    # ---------------
    # Training
    # ---------------

    # ---------------
    # .Evaluation
    # ---------------
    class ResponseEvaluation(Enum):
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
