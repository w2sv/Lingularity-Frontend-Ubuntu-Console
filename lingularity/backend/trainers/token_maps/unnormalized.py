from itertools import chain
from typing import List, Dict, Optional

import numpy as np
from tqdm import tqdm

from lingularity.backend.trainers.token_maps.base import Token2SentenceIndicesMap
from lingularity.backend.utils.strings import get_meaningful_tokens


class UnnormalizedToken2SentenceIndices(Token2SentenceIndicesMap):
    """ dict with
            keys: String = distinct lowercase, punctuation-stripped, digit-free foreign language tokens
            values: List[int] = lists of sentence indices in which appearing """

    def __init__(self, sentence_data: np.ndarray, discard_proper_nouns=True):
        super().__init__()

        self._sentence_data = sentence_data

        print('Mapping tokens...')
        for i, sentence in enumerate(tqdm(self._sentence_data[:, 1])):
            # split, discard impertinent characters, lower all
            for token in (token.lower() for token in get_meaningful_tokens(sentence)):
                if len(token) and not any(i.isdigit() for i in token):
                    self.upsert(token, i)

        print('Discarding proper nouns...')
        if discard_proper_nouns:
            for proper_noun in self._get_proper_nouns():
                self.pop(proper_noun, None)

    # ----------------
    # PROPER NOUN QUERY
    # ----------------
    def _get_proper_nouns(self) -> List[str]:
        name_candidates_2_sentence_indices = self._title_based_proper_noun_retrieval()
        return list(self._bilateral_presence_based_proper_noun_filtering(name_candidates_2_sentence_indices))

    def _title_based_proper_noun_retrieval(self) -> Dict[str, int]:
        """ Returns:
                lowercase name candidates """

        names_2_sentenceindex = {}
        for i, eng_sent in enumerate(tqdm(self._sentence_data[:, 0])):
            tokens = get_meaningful_tokens(eng_sent)
            [names_2_sentenceindex.update({name.lower(): i}) for name in filter(lambda token: token.istitle() and (len(token) > 1 or ord(token) > 255), tokens)]
        return names_2_sentenceindex

    def _bilateral_presence_based_proper_noun_filtering(self, namecandidate_2_sentenceind: Dict[str, int]) -> List[str]:
        """ returns lowercase names """

        return list(np.asarray(list(filter(lambda item: item[0] in map(lambda token: token.lower(), get_meaningful_tokens(self._sentence_data[item[1]][1])), list(namecandidate_2_sentenceind.items()))))[:, 0])

    # ----------------
    # Indices Query
    # ----------------
    def get_comprising_sentence_indices(self, article_stripped_token: str) -> Optional[List[int]]:
        indices = list(chain.from_iterable([v for k, v in self.items() if any(token.startswith(article_stripped_token) for token in k.split(' '))]))
        return indices if len(indices) else None