import numpy as np

from .base import TokenMap
from .unnormalized import UnnormalizedTokenMap
from .normalized import StemMap, LemmaMap


def get_token_map(sentence_data: np.ndarray, language: str, load_normalizer=True) -> TokenMap:
    for cls in [LemmaMap, StemMap]:
        if cls.is_available(language):  # type: ignore
            return cls(sentence_data, language, load_normalizer=load_normalizer)

    return UnnormalizedTokenMap(sentence_data)
