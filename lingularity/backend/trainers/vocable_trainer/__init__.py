from typing import List, Optional, Sequence, Dict, Iterator, Tuple
from itertools import starmap, tee
from collections import defaultdict

import numpy as np

from .deviation_masks import deviation_masks
from .response_evaluation import ResponseEvaluation, get_response_evaluation
from lingularity.backend.components.vocable_entry import VocableData, VocableEntry
from lingularity.backend.components import SentenceData, TokenMap, get_token_map
from lingularity.backend.trainers.base import TrainerBackend
from lingularity.backend.database import MongoDBClient


class VocableTrainerBackend(TrainerBackend):
    def __init__(self, non_english_language: str, train_english: bool):
        super().__init__(non_english_language, train_english)

        self._sentence_data: SentenceData = self._get_sentence_data()
        self._token_2_sentence_indices: TokenMap = get_token_map(self._sentence_data, self.language, load_normalizer=True)

        self.synonyms: Optional[Dict[str, List[str]]] = None
        self.new_vocable_entries: Optional[Iterator[VocableEntry]] = None

    @staticmethod
    def get_eligible_languages() -> List[str]:
        return MongoDBClient.get_instance().query_vocabulary_possessing_languages()

    @property
    def new_vocable_entries_available(self) -> bool:
        assert self.new_vocable_entries is not None

        self.new_vocable_entries, teed = tee(self.new_vocable_entries)
        return next(teed, None) is not None

    # ---------------
    # Pre Training
    # ---------------
    def set_item_iterator(self):
        """ Additionally sets synonyms, new_vocable_entries iterator """

        vocable_entries_to_be_trained = self._vocable_entries_to_be_trained()

        self.synonyms = self._find_synonyms(vocable_entries_to_be_trained)
        self.new_vocable_entries = filter(lambda entry: entry.is_new, vocable_entries_to_be_trained)
        self._set_item_iterator(vocable_entries_to_be_trained)

    def _vocable_entries_to_be_trained(self) -> List[VocableEntry]:
        tokens_with_vocable_data: Iterator[Tuple[str, VocableData]] = filter(lambda token_with_data: not VocableEntry.is_perfected(data=token_with_data[1]), self.mongodb_client.query_vocabulary())
        return list(starmap(VocableEntry, tokens_with_vocable_data))

    @staticmethod
    def _find_synonyms(vocable_entries: List[VocableEntry]) -> Dict[str, List[str]]:
        """ Returns:
                Dict[english_meaning: [synonym_1, synonym_2, ..., synonym_n]]

                for n >= 2 synonyms contained within retrieved vocable entries possessing the IDENTICAL
                english the-stripped meaning"""

        meaning_2_vocables = defaultdict(list)

        for entry in vocable_entries:
            meaning_2_vocables[entry.the_stripped_meaning].append(entry.vocable)

        return {meaning: synonyms for meaning, synonyms in meaning_2_vocables.items() if len(synonyms) >= 2}

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
