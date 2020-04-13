from typing import List, Tuple, Dict
from operator import itemgetter
from itertools import chain

from .utils.statistics import get_outliers
from .utils.generic import append_2_or_insert_key


class TokenSentenceindicesMap(Dict):
    def get_sorted_token_n_occurrences_list(self) -> List[Tuple[str, int]]:
        return [(i[0], len(i[1])) for i in sorted(list(self.items()), key=lambda x: len(x[1]))]

    def get_n_occurrences_2_tokens_map(self) -> Dict[int, List[str]]:
        occurrence_2_tokens = {}
        for token, inds in self.items():
            append_2_or_insert_key(occurrence_2_tokens, len(inds), token)
        return occurrence_2_tokens

    def discard_positive_outliers(self):
        noccurrence_2_tokens = self.get_n_occurrences_2_tokens_map()
        occurrence_outliers = get_outliers(list(noccurrence_2_tokens.keys()), positive=True, iqr_coeff=0.2)
        corresponding_tokens = chain.from_iterable(itemgetter(*occurrence_outliers)(noccurrence_2_tokens))
        [self.pop(outlier_token) for outlier_token in corresponding_tokens]

    @classmethod
    def get_negative_outliers(self):
        noccurrence_2_tokens = self.get_n_occurrences_2_tokens_map()
        occurrence_outliers = get_outliers(list(noccurrence_2_tokens.keys()), positive=False, iqr_coeff=0)
        corresponding_tokens = chain.from_iterable((noccurrence_2_tokens[occ_out] for occ_out in occurrence_outliers))
        return {token: self[token] for token in corresponding_tokens}
