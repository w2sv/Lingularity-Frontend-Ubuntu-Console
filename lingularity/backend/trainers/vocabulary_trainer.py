from typing import List, Dict, Optional, Any
from collections import Counter

import unidecode
import numpy as np

from lingularity.backend.trainers.base import TrainerBackend
from lingularity.backend.types.token_maps import RawToken2SentenceIndices
from lingularity.database import MongoDBClient
from lingularity.utils.strings import get_article_stripped_token
from lingularity.utils.enum import ExtendedEnum


class VocabularyTrainerBackend(TrainerBackend):
    class ResponseEvaluation(ExtendedEnum):
        Wrong = 0
        AccentError = 0.5
        AlmostCorrect = 0.5
        Perfect = 1

    class VocableEntry:
        RawType = Dict[str, Dict[str, Any]]
        REFERENCE_TO_FOREIGN: Optional[bool] = None

        def __init__(self, entry: RawType):
            self._entry = entry

        @property
        def token(self) -> str:
            return next(iter(self._entry.keys()))

        @property
        def display_token(self) -> str:
            return self.translation if not self.REFERENCE_TO_FOREIGN else self.token

        @property
        def translation(self) -> str:
            return self._entry[self.token]['t']

        @property
        def display_translation(self) -> str:
            return self.translation if self.REFERENCE_TO_FOREIGN else self.token

        @property
        def last_faced_date(self) -> Optional[str]:
            return self._entry[self.token]['lfd']

        def __str__(self):
            return str(self._entry)

    def __init__(self, non_english_language: str, train_english: bool):
        super().__init__(non_english_language, train_english)

        self._sentence_data = self._parse_sentence_data()
        self._token_2_rowinds = RawToken2SentenceIndices(self._sentence_data, language=self.language)
        self._vocable_entries: List[VocabularyTrainerBackend.VocableEntry] = self._get_vocable_entries()
        np.random.shuffle(self._vocable_entries)

    @staticmethod
    def get_vocabulary_possessing_languages():


    # ---------------
    # INITIALIZATION
    # ---------------
    def _get_vocable_entries(self) -> List[VocableEntry]:
        self.VocableEntry.REFERENCE_TO_FOREIGN = self._train_english
        return list(map(self.VocableEntry, self.mongodb_client.query_vocabulary_data()))

    def _get_reponse_evaluation(self, response: str, translation: str) -> ResponseEvaluation:
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

    def _get_related_sentences(self, token: str) -> Optional[List[str]]:
        WORD_ROOT_LENGTH = 4

        root = get_article_stripped_token(token)[:WORD_ROOT_LENGTH]
        sentence_indices = np.asarray(self._token_2_rowinds.get_root_comprising_sentence_indices(root))
        if not len(sentence_indices):
            return None

        random_indices = np.random.randint(0, len(sentence_indices), self.N_RELATED_SENTENCES)
        return self._sentence_data[sentence_indices[random_indices]][:, 1]

    # -----------------
    # PROGRAM TERMINATION
    # -----------------
    @property
    def correctness_percentage(self) -> float:
        return self._n_correct_responses / self._n_trained_items * 100

    @property
    def performance_verdict(self) -> str:
        return {
            0: 'You suck.',
            20: 'Get your shit together m8.',
            40: "You can't climb the ladder of success with your hands in your pockets.",
            60: "Keep hustlin' young blood.",
            80: 'Attayboy!',
            100: '0361/2680494. Call me.'}[int(self.correctness_percentage) // 20 * 20]
