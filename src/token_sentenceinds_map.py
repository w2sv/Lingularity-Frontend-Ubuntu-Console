from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Optional, AbstractSet, ValuesView, Any, Iterator
from operator import itemgetter
from itertools import chain, groupby
from functools import lru_cache
from collections.abc import MutableMapping
from collections import Mapping

from tqdm import tqdm
import numpy as np
import nltk

from .utils.statistics import get_outliers
from .utils.generic import append_2_or_insert_key
from .utils.strings import get_meaningful_tokens, strip_unicode


class CustomDict(MutableMapping, ABC):
    def __init__(self, mapping_data: Optional[MutableMapping] = None):
        self.mapping = {}
        self.update(mapping_data)

    def __getitem__(self, key):
        return self.mapping[key]

    def __setitem__(self, key, value):
        self.mapping[key] = value

    def __delitem__(self, key):
        del self.mapping[key]

    def __iter__(self):
        return iter(self.mapping)

    def __len__(self):
        return len(self.mapping)

    def __str__(self):
        return str(self.mapping)

    def items(self) -> AbstractSet[Tuple[Any, Any]]:
        return self.mapping.items()

    def keys(self) -> AbstractSet[Any]:
        return self.mapping.keys()

    def values(self) -> ValuesView[Any]:
        return self.mapping.values()


class IterableKeyDict(CustomDict):
    def __init__(self, mapping_data: Optional[MutableMapping] = None):
        super().__init__(mapping_data)

    def append_or_insert(self, key, value):
        if key in self:
            if not hasattr('__iter__', value):
                self[key].append(value)
            else:
                self[key].extend(value)
        else:
            self[key] = [value]


class FrozenIterableKeyDict(Mapping):
    pass


class Token2Indices(IterableKeyDict):
    def __init__(self, mapping_data: Optional[MutableMapping] = None):
        super().__init__(mapping_data)
        self.initialize()

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
    @lru_cache()
    def occurrences_2_tokens(self) -> Dict[int, List[str]]:
        # TODO: implement frozen, hence hashable dict
        occurrence_2_tokens = {}
        for token, indices in self.items():
            append_2_or_insert_key(occurrence_2_tokens, len(indices), token)
        return occurrence_2_tokens

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

        print('Parsing data...')
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

        self.names: Optional[List[str]] = None
        super().__init__()

    @classmethod
    def from_sentence_data(cls, sentence_data: np.ndarray, stemmer: Optional[nltk.stem.SnowballStemmer]):
        return cls(RawToken2SentenceIndices(sentence_data), stemmer)

    def __getattr__(self, item):
        return dir(self.raw_token_map)[item]

    def initialize(self):
        stemming_possible = self.stemmer is not None
        self.names = self.get_proper_nouns()

        starting_letter_grouped_names: Dict[str, List[str]] = {k: list(v) for k, v in groupby(sorted(self.names), lambda name: name[0])}

        print('Name Dismissal, Stemming...') if stemming_possible else print('Name Dismissal...')
        for token, indices in tqdm(list(self.raw_token_map.items())):
            if starting_letter_grouped_names.get(token[0]) is not None and token in starting_letter_grouped_names[token[0]]:
                continue
            if stemming_possible:
                token = self.stemmer.stem(token)
            self.append_or_insert(token, indices)

    # ----------------
    # PROPER NOUN QUERY
    # ----------------
    def get_proper_nouns(self) -> List[str]:
        # TODO: possibly refactor to tuple property
        name_candidates_2_sentence_indices = self._title_based_proper_noun_retrieval()
        return self._bilateral_presence_based_proper_noun_filtering(name_candidates_2_sentence_indices)

    def _title_based_proper_noun_retrieval(self) -> Dict[str, int]:
        """ returns lowercase name candidates """
        names_2_occurrenceind = {}
        print('Procuring names...')
        for i, eng_sent in enumerate(tqdm(self.sentence_data[:, 0])):
            tokens = get_meaningful_tokens(eng_sent)
            [names_2_occurrenceind.update({name.lower(): i}) for name in filter(lambda token: token.istitle() and (len(token) > 1 or ord(token) > 255), tokens)]
        return names_2_occurrenceind

    def _bilateral_presence_based_proper_noun_filtering(self, namecandidate_2_sentenceind: Dict[str, int]) -> List[str]:
        """ returns lowercase names """
        return list(np.array(list(filter(lambda item: item[0] in map(lambda token: token.lower(), get_meaningful_tokens(self.sentence_data[item[1]][1])), list(namecandidate_2_sentenceind.items()))))[:, 0])


if __name__ == '__main__':
    dic = CustomDict({3: 5, 5: 9})
    print(dic.get(4))
