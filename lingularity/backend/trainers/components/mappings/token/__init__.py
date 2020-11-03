from typing import Tuple

from .occurrences import TokenOccurrencesMap
from .sentence_indices import (
    get_token_sentence_indices_map,
    SegmentSentenceIndicesMap
)


def get_token_maps(language: str) -> Tuple[SegmentSentenceIndicesMap, TokenOccurrencesMap]:
    return get_token_sentence_indices_map(language, load_normalizer=False), TokenOccurrencesMap(language)
