from typing import *
from abc import ABC, abstractmethod
from collections import defaultdict
from itertools import repeat

from lingularity.backend.utils import strings, iterables
from lingularity.backend.trainers.components.mappings.base import CustomMapping, _display_creation_kickoff_message


SentenceIndex2UniqueTokens = Dict[int, Set[str]]


class SegmentSentenceIndicesMap(defaultdict, CustomMapping, ABC):
    """ Interface for map classes comprising an association of
          unique, LOWERCASE and RELEVANT tokens (unnormalized/normalized): str
                to the
          sentence indices corresponding to the bilateral sentence data in
          which they occur, in either an inflected form (NormalizedTokenMaps)
          or as they are(TokenSentenceIndicesMap): List[int] """

    _Type = Dict[str, List[int]]

    def __init__(self, language: str, create: bool):
        super().__init__(list, self._data(language, create=create))

    @_display_creation_kickoff_message('Creating {}...')
    def create(self, sentence_index_2_unique_tokens: SentenceIndex2UniqueTokens):
        for sentence_index, tokens in sentence_index_2_unique_tokens.items():
            for token in tokens:
                self[token].append(sentence_index)

    def tokenize_with_pos_tags(self, sentence: str) -> List[Tuple[str, str]]:
        # TODO: Implement in spacy devoid fashion

        return list(zip(self.tokenize(sentence), repeat('')))

    @abstractmethod
    def tokenize(self, sentence: str) -> List[str]:
        pass

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
                    -> return None if no sentence indices found at all
                - consecutively pop sentence indices element from sentence indices list, starting with the
                    ones corresponding to tokens of lower relevance, and return the intersection between
                    the remaining sentence indices elements if existent
                - return sentence indices of most relevant vocable if the only one remaining """

        relevance_sorted_sentence_indices = iterables.none_stripped((self.get(token) for token in relevance_sorted_tokens))

        if not len(relevance_sorted_sentence_indices):
            return None

        relevance_sorted_sentence_indices = list(map(set, relevance_sorted_sentence_indices))
        while len(relevance_sorted_sentence_indices) > 1:
            if len((remaining_sentence_indices_list_intersection := iterables.iterables_intersection(relevance_sorted_sentence_indices))):
                return list(remaining_sentence_indices_list_intersection)
            relevance_sorted_sentence_indices.pop()

        return list(relevance_sorted_sentence_indices[0])

    @staticmethod
    def _get_length_sorted_meaningful_tokens(vocable_entry: str) -> List[str]:
        if (article_stripped_noun := strings.get_article_stripped_noun(vocable_entry)) is not None:
            return [article_stripped_noun]
        return sorted(strings.get_meaningful_tokens(vocable_entry, apostrophe_splitting=True), key=lambda token: len(token))
