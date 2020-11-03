from typing import *

from collections import defaultdict

from lingularity.backend.utils import iterables
from lingularity.backend.trainers.components import SentenceData
from lingularity.backend.trainers.components.mappings.token import (
    get_token_maps,
    TokenOccurrencesMap,
    SegmentSentenceIndicesMap
)


def filter_sentence_data(sentence_data: SentenceData, language: str) -> SentenceData:
    sentence_indices_map, occurrences_map = get_token_maps(language)

    sentence_indices_with_comprising_occurrences = _sentence_indices_with_comprising_tokens(sentence_indices_map, occurrences_map)
    sentence_indices = (sentence_index for sentence_index, comprising_occurrences in sentence_indices_with_comprising_occurrences if all((occurrence >= occurrences_map.occurrence_mean for occurrence in comprising_occurrences)))
    return sentence_data[list(sentence_indices)]


def _sentence_indices_with_comprising_tokens(sentence_indices_map: SegmentSentenceIndicesMap,
                                             occurrences_map: TokenOccurrencesMap) -> Iterator[Tuple[int, Iterator[int]]]:

    sentence_index_2_comprising_tokens: Dict[int, Set[str]] = defaultdict(set)
    for token, sentence_indices in sentence_indices_map.items():
        for sentence_index in sentence_indices:
            sentence_index_2_comprising_tokens[sentence_index].add(token)

    return ((sentence_index, iterables.none_stripped(map(occurrences_map.get, comprising_tokens))) for sentence_index, comprising_tokens in sentence_index_2_comprising_tokens.items())  # type: ignore
