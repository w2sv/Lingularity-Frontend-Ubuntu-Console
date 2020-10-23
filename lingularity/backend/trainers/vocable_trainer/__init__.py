from typing import List, Optional, Sequence
from itertools import repeat, starmap
from functools import cached_property

import numpy as np

from .response_evaluation import ResponseEvaluation, get_response_evaluation
from lingularity.backend.components import SentenceData, VocableEntry, TokenMap, get_token_map
from lingularity.backend.trainers.base import TrainerBackend
from lingularity.backend.database import MongoDBClient


class VocableTrainerBackend(TrainerBackend):
    def __init__(self, non_english_language: str, train_english: bool):
        super().__init__(non_english_language, train_english)

        self._training_items: Optional[List[VocableEntry]] = None
        self._sentence_data: SentenceData = self._get_sentence_data()
        self._token_2_sentence_indices: TokenMap = get_token_map(self._sentence_data, self.language, load_normalizer=True)

    @staticmethod
    def get_eligible_languages() -> List[str]:
        return MongoDBClient.get_instance().query_vocabulary_possessing_languages()

    def set_item_iterator(self):
        self._training_items = self._get_imperfect_vocable_entries()
        self._set_item_iterator(self._training_items)

    def _get_imperfect_vocable_entries(self) -> List[VocableEntry]:
        entire_vocabulary = starmap(VocableEntry, zip(self.mongodb_client.query_vocabulary_data(), repeat(self._train_english)))
        return list(filter(lambda vocable_entry: not vocable_entry.is_perfected, entire_vocabulary))

    # ---------------
    # Pre Training
    # ---------------
    @cached_property
    def new_vocable_entries(self) -> List[VocableEntry]:
        assert self._training_items is not None

        return list(filter(lambda entry: entry.is_new, self._training_items))

    # ---------------
    # Training
    # ---------------
    def related_sentence_pairs(self, entry: str, n: int) -> Sequence[Sequence[str]]:
        if (sentence_indices := self._token_2_sentence_indices.query_sentence_indices(entry)) is None:
            return []

        sentence_indices = np.asarray(sentence_indices)
        np.random.shuffle(sentence_indices)

        assert sentence_indices is not None

        return self._sentence_data[sentence_indices[:n]]
