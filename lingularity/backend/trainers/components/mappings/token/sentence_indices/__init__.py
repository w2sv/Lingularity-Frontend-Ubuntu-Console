from .base import SegmentSentenceIndicesMap
from .unnormalized import TokenSentenceIndicesMap
from .normalized import (
    NormalizedTokenSentenceIndicesMap,
    StemSentenceIndicesMap,
    LemmaSentenceIndicesMap
)


def get_token_sentence_indices_map(language: str, load_normalizer=True) -> SegmentSentenceIndicesMap:
    for cls in [LemmaSentenceIndicesMap, StemSentenceIndicesMap]:
        if cls.is_available(language):  # type: ignore
            return cls(language, load_normalizer=load_normalizer)

    return TokenSentenceIndicesMap(language)
