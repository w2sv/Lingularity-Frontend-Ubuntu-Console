from .base import TokenSentenceIndicesMap
from .unnormalized import UnnormalizedTokenSentenceIndicesMap
from .normalized import (
    NormalizedTokenSentenceIndicesMap,
    StemSentenceIndicesMap,
    LemmaSentenceIndicesMap
)


def get_token_sentence_indices_map(language: str, load_normalizer=True) -> TokenSentenceIndicesMap:
    for cls in [LemmaSentenceIndicesMap, StemSentenceIndicesMap]:
        if cls.is_available(language):  # type: ignore
            return cls(language, load_normalizer=load_normalizer)

    return UnnormalizedTokenSentenceIndicesMap()
