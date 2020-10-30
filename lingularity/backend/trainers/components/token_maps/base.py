from typing import DefaultDict, Optional, List, Dict
from abc import ABC, abstractmethod
from collections import defaultdict

import numpy as np

from lingularity.backend.utils import either
from lingularity.backend.utils.strings import split_at_uppercase, get_meaningful_tokens, get_article_stripped_noun
from lingularity.backend.utils.iterables import iterables_intersection, none_stripped


class TokenMap(defaultdict, ABC):
    """ Interface for map classes comprising an association of
          unique, LOWERCASE and RELEVANT tokens (unnormalized/normalized): str
                to the
          sentence indices corresponding to the bilateral sentence data in
          which they occur, in either an inflected form (NormalizedTokenMaps)
          or as they are(UnnormalizedTokenMap): List[int] """

    Type = Dict[str, List[int]]
    OccurrenceMap = DefaultDict[str, int]

    def __init__(self, data: Optional[Type] = None, occurrence_map: Optional[OccurrenceMap] = None):
        super().__init__(list, either(data, default={}))

        self.occurrence_map: TokenMap.OccurrenceMap = either(occurrence_map, default=defaultdict(lambda: 0))

    @abstractmethod
    def _map_tokens(self, sentence_data: np.ndarray):
        """ Sets both data and occurrence map """
        pass

    def _display_mapping_initialization_message(self):
        print(f'Creating {" ".join(split_at_uppercase(self.__class__.__name__))}s...')

    def _get_data(self) -> Dict[str, List[int]]:
        return {**self}

    # ------------------
    # Sentence Index Query
    # ------------------
    @abstractmethod
    def query_sentence_indices(self, vocable_entry: str) -> Optional[List[int]]:
        """ Queries indices of sentences in which the relevant tokens of the passed vocable_entry occur

            Args:
                vocable_entry: raw vocable entry of the same language as the tokens present in map """
        pass

    def _find_best_fit_sentence_indices(self, relevance_sorted_tokens: List[str]) -> Optional[List[int]]:
        """ Working Principle:
                - query sentence indices corresponding to distinct tokens present in relevance_sorted_tokens
                - return None if no sentence indices found at all
                - consecutively pop sentence indices element from sentence indices list, starting with the
                    ones corresponding to tokens of lower relevance, and return the intersection between
                    the remaining sentence indices elements if existent
                - return sentence indices of most relevant vocable if the only one remaining """

        relevance_sorted_sentence_indices = none_stripped((self.get(token) for token in relevance_sorted_tokens))

        if not len(relevance_sorted_sentence_indices):
            return None

        relevance_sorted_sentence_indices = list(map(set, relevance_sorted_sentence_indices))
        while len(relevance_sorted_sentence_indices) > 1:
            if len((remaining_sentence_indices_list_intersection := iterables_intersection(
                    relevance_sorted_sentence_indices))):
                return list(remaining_sentence_indices_list_intersection)
            relevance_sorted_sentence_indices.pop()

        return list(relevance_sorted_sentence_indices[0])

    @staticmethod
    def _get_length_sorted_meaningful_tokens(vocable_entry: str) -> List[str]:
        if (article_stripped_noun := get_article_stripped_noun(vocable_entry)) is not None:
            return [article_stripped_noun]
        return sorted(get_meaningful_tokens(vocable_entry, apostrophe_splitting=True), key=lambda token: len(token))
