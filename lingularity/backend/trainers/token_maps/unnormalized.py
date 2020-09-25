from typing import List, Set, Optional

import numpy as np
from tqdm import tqdm

from lingularity.backend.trainers.token_maps.base import TokenMap
from lingularity.backend.utils.strings import get_meaningful_tokens, is_digit_free


class UnnormalizedTokenMap(TokenMap):
    """ keys: punctuation-stripped, proper noun-stripped, digit-free tokens """

    def __init__(self, sentence_data: np.ndarray, apostrophe_splitting=True):
        super().__init__()

        self._apostrophe_splitting = apostrophe_splitting
        self._map_tokens(sentence_data)

    def _map_tokens(self, sentence_data: np.ndarray):
        proper_nouns = self._get_proper_nouns(sentence_data)

        self._output_mapping_initialization_message()
        for i, sentence in enumerate(tqdm(sentence_data[:, 1])):
            for token in (token.lower() for token in get_meaningful_tokens(sentence, self._apostrophe_splitting)):
                if len(token) and is_digit_free(token) and token not in proper_nouns:
                    self[token].append(i)
                    self.occurrence_map[token] += 1

    @staticmethod
    def _get_proper_nouns(sentence_data: np.ndarray) -> Set[str]:
        """ Working principle:
                for each sentence pair:
                    - get set of intersection between tokens of english sentence and its translation
                    - add tokens
                        starting on an uppercase characters
                        being either comprised of at least 2 characters or non-latin

            Returns:
                set of lowercase proper nouns """

        proper_nouns = set()

        print('Procuring proper nouns...')
        for sentence_pair in tqdm(sentence_data):
            proper_noun_candidates = set.intersection(*map(lambda sentence: set(get_meaningful_tokens(sentence)), sentence_pair))
            for candidate in proper_noun_candidates:
                if candidate.istitle() and len(candidate) > 1:
                    proper_nouns.add(candidate.lower())

        return proper_nouns

    # ----------------
    # Query
    # ----------------
    def query_sentence_indices(self, vocable_entry: str) -> Optional[List[int]]:
        return self._find_best_fit_sentence_indices(relevance_sorted_tokens=self._get_length_sorted_meaningful_tokens(vocable_entry))
