from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Optional, Iterator
from operator import itemgetter
from itertools import chain, groupby
from collections.abc import MutableMapping

from tqdm import tqdm
import numpy as np
import nltk

from .dictionary_abstractions import CustomDict
from .utils.statistics import get_outliers
from .utils.strings import get_meaningful_tokens, strip_unicode


class Token2Indices(CustomDict):
    def __init__(self, mapping_data: Optional[MutableMapping] = None):
        super().__init__(mapping_data)
        self.initialize()

        self._occurrence_2_tokens: Optional[CustomDict[int, List[str]]] = None

    # -----------------
    # TOKEN QUERY
    # -----------------
    def get_root_comprising_tokens(self, root) -> List[str]:
        return [k for k in self.keys() if root in k]

    # -----------------
    # ROOT BASED SENTENCE INDEX QUERY
    # -----------------
    def get_root_comprising_sentence_indices(self, root: str) -> List[int]:
        return list(chain.from_iterable([v for k, v in self.items() if root in k]))

    def get_root_preceded_token_comprising_sentence_indices(self, root: str) -> List[int]:
        """ unused """
        return list(chain.from_iterable([v for k, v in self.items() if any(token.startswith(root) for token in k.split(' '))]))

    # -----------------
    # TOKEN OCCURRENCES
    # -----------------
    def get_sorted_token_n_occurrences_list(self) -> List[Tuple[str, int]]:
        return [(i[0], len(i[1])) for i in sorted(list(self.items()), key=lambda x: len(x[1]))]

    @property
    def occurrences_2_tokens(self) -> CustomDict:  # [int, List[str]]
        if self._occurrence_2_tokens is None:
            self._occurrence_2_tokens = CustomDict()
            for token, indices in self.items():
                self._occurrence_2_tokens.append_or_insert(len(indices), token)
        return self._occurrence_2_tokens

    # ----------------
    # OCCURRENCE OUTLIER BASED
    # ----------------
    def _get_occurrence_outlier_corresponding_tokens(self, occurrence_outliers: List[int]) -> Iterator[str]:
        return chain.from_iterable(itemgetter(*occurrence_outliers)(self.occurrences_2_tokens))

    def pop_positive_occurrence_outliers(self, iqr_coefficient: float = 0.2):
        occurrence_outliers = get_outliers(list(self.occurrences_2_tokens.keys()), positive=True, iqr_coeff=iqr_coefficient)
        corresponding_tokens = self._get_occurrence_outlier_corresponding_tokens(occurrence_outliers)
        [self.pop(outlier_token) for outlier_token in corresponding_tokens]

    def get_negative_occurrence_outliers(self, iqr_coefficient: float = 0):  # -> Token2IndicesBase
        occurrence_outliers = get_outliers(list(self.occurrences_2_tokens.keys()), positive=False, iqr_coeff=iqr_coefficient)
        corresponding_tokens = self._get_occurrence_outlier_corresponding_tokens(occurrence_outliers)
        return {token: self[token] for token in corresponding_tokens}

    # ----------------
    # ABSTRACTS
    # ----------------
    @abstractmethod
    def initialize(self):
        pass


class RawToken2SentenceIndices(Token2Indices):
    def __init__(self, sentence_data: np.ndarray):
        self.sentence_data = sentence_data
        super().__init__()

    def initialize(self):
        """ returns dict with
                keys: distinct lowercase delimiter split punctuation stripped foreign language vocabulary tokens
                    excluding numbers
                values: lists of sentence indices in which occurring """

        print('Mapping tokens...')
        for i, sentence in enumerate(tqdm(self.sentence_data[:, 1])):
            # split, discard impertinent characters, lower all
            tokens = (token.lower() for token in get_meaningful_tokens(sentence))
            for token in tokens:
                if not len(token) or any(i.isdigit() for i in token):
                    continue
                self.append_or_insert(token, i)


class Stem2SentenceIndices(Token2Indices):
    def __init__(self, raw_token_map: RawToken2SentenceIndices, stemmer: Optional[nltk.stem.SnowballStemmer]):
        self.raw_token_map: RawToken2SentenceIndices = raw_token_map
        self.stemmer: Optional[nltk.stem.SnowballStemmer] = stemmer
        self._proper_nouns: Optional[List[str]] = None
        super().__init__()

    @classmethod
    def from_sentence_data(cls, sentence_data: np.ndarray, stemmer: Optional[nltk.stem.SnowballStemmer]):
        return cls(RawToken2SentenceIndices(sentence_data), stemmer)

    def __getattr__(self, item):
        """ forwarding sentence_data calls """
        return getattr(self.raw_token_map, item)

    def initialize(self):
        stemming_possible = self.stemmer is not None

        starting_letter_grouped_names: Dict[str, List[str]] = {k: list(v) for k, v in groupby(sorted(self.proper_nouns), lambda name: name[0])}

        print('Discarding proper nouns, stemming...') if stemming_possible else print('Discarding proper nouns...')
        for token, indices in tqdm(list(self.raw_token_map.items())):
            if starting_letter_grouped_names.get(token[0]) is not None and token in starting_letter_grouped_names[token[0]]:
                continue
            if stemming_possible:
                token = self.stemmer.stem(token)
            self.append_or_insert(token, indices)

    # ----------------
    # PROPER NOUN QUERY
    # ----------------
    @property
    def proper_nouns(self) -> List[str]:
        if self._proper_nouns is None:
            name_candidates_2_sentence_indices = self._title_based_proper_noun_retrieval()
            self._proper_nouns = list(self._bilateral_presence_based_proper_noun_filtering(name_candidates_2_sentence_indices))
        return self._proper_nouns

    def _title_based_proper_noun_retrieval(self) -> Dict[str, int]:
        """ returns lowercase name candidates """
        names_2_sentenceind = {}
        print('Procuring proper nouns...')
        for i, eng_sent in enumerate(tqdm(self.sentence_data[:, 0])):
            tokens = get_meaningful_tokens(eng_sent)
            [names_2_sentenceind.update({name.lower(): i}) for name in filter(lambda token: token.istitle() and (len(token) > 1 or ord(token) > 255), tokens)]
        return names_2_sentenceind

    def _bilateral_presence_based_proper_noun_filtering(self, namecandidate_2_sentenceind: Dict[str, int]) -> List[str]:
        """ returns lowercase names """
        return list(np.array(list(filter(lambda item: item[0] in map(lambda token: token.lower(), get_meaningful_tokens(self.sentence_data[item[1]][1])), list(namecandidate_2_sentenceind.items()))))[:, 0])


if __name__ == '__main__':
    pass
