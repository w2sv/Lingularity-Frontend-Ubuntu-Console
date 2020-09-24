from typing import DefaultDict, Optional, List
from abc import ABC, abstractmethod
from collections import defaultdict

import numpy as np

from lingularity.backend.utils.strings import split_at_uppercase, get_meaningful_tokens, get_article_stripped_token
from lingularity.backend.utils.iterables import iterables_intersection, none_stripped


class CustomDict(ABC):
    def __getattr__(self, item):
        return getattr(self._map, item)

    def __getitem__(self, item):
        return self._map[item]

    def __setitem__(self, item, value):
        self._map[item] = value

    def __str__(self):
        return str(self._map)


class TokenMap(CustomDict, ABC):
    def __init__(self):
        self._map: DefaultDict[str, List[int]] = defaultdict(list)
        self.occurrence_map: DefaultDict[str, int] = defaultdict(lambda: 0)

    @abstractmethod
    def _map_tokens(self, sentence_data: np.ndarray):
        pass

    def _output_mapping_initialization_message(self):
        print(f'Creating {" ".join(split_at_uppercase(self.__class__.__name__))}s...')

    # ------------------
    # Query
    # ------------------
    @abstractmethod
    def get_comprising_sentence_indices(self, vocable_entry: str) -> Optional[List[int]]:
        pass

    def _find_best_fit_sentence_indices(self, relevance_sorted_tokens: List[str]) -> Optional[List[int]]:
        relevance_sorted_sentence_indices = none_stripped((self.get(token) for token in relevance_sorted_tokens))

        if not len(relevance_sorted_sentence_indices):
            return None

        relevance_sorted_sentence_indices = list(map(set, relevance_sorted_sentence_indices))
        while len(relevance_sorted_sentence_indices) > 1:
            if len((remaining_sentence_indices_list_intersection := iterables_intersection(
                    relevance_sorted_sentence_indices))):
                return list(remaining_sentence_indices_list_intersection)
            relevance_sorted_sentence_indices.pop()

        return list(relevance_sorted_sentence_indices.pop())

    @staticmethod
    def _get_length_sorted_meaningful_tokens(vocable_entry: str) -> List[str]:
        if len((article_stripped_token := get_article_stripped_token(vocable_entry))) == 1:
            return [article_stripped_token]
        return sorted(get_meaningful_tokens(vocable_entry), key=lambda token: len(token))
