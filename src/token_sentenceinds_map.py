from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Optional, AbstractSet, ValuesView, Any
from operator import itemgetter
from itertools import chain, groupby
from collections.abc import MutableMapping

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


class Token2IndicesBase(CustomDict):
    def __init__(self, mapping_data: Optional[MutableMapping] = None):
        super().__init__(mapping_data)

    def append_or_insert(self, key, value):
        """ assert that mapping values iterable """
        if key in self:
            if not hasattr('__iter__', value):
                self[key].append(value)
            else:
                self[key].extend(value)
        else:
            self[key] = [value]

    @abstractmethod
    def initialize(self):
        pass

    def get_sorted_token_n_occurrences_list(self) -> List[Tuple[str, int]]:
        return [(i[0], len(i[1])) for i in sorted(list(self.items()), key=lambda x: len(x[1]))]

    def get_n_occurrences_2_tokens_map(self) -> Dict[int, List[str]]:
        occurrence_2_tokens = {}
        for token, indices in self.items():
            append_2_or_insert_key(occurrence_2_tokens, len(indices), token)
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


class Token2SentenceIndices(Token2IndicesBase):
    def __init__(self, sentence_data: np.ndarray):
        super().__init__()
        self.sentence_data = sentence_data
        self.initialize()

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


class Stem2SentenceIndices(Token2IndicesBase):
    def __init__(self, raw_token_map: Token2SentenceIndices, stemmer: Optional[nltk.stem.SnowballStemmer]):
        super().__init__()
        self.raw_token_map: Token2SentenceIndices = raw_token_map
        self.stemmer: Optional[nltk.stem.SnowballStemmer] = stemmer

        self.names: Optional[List[str]] = None

        self.initialize()

    def __getattr__(self, item):
        return dir(self.raw_token_map)[item]

    def initialize(self):
        stemming_possible = self.stemmer is not None
        self.names = self.get_names()

        starting_letter_grouped_names: Dict[str, List[str]] = {k: list(v) for k, v in groupby(sorted(self.names), lambda name: name[0])}

        print('Name Dismissal, Stemming...') if stemming_possible else print('Name Dismissal...')
        for token, indices in tqdm(list(self.raw_token_map.items())):
            if starting_letter_grouped_names.get(token[0]) is not None and token in starting_letter_grouped_names[token[0]]:
                continue
            if stemming_possible:
                token = self.stemmer.stem(token)
            self.append_or_insert(token, indices)

    def get_names(self) -> List[str]:
        name_candidates_2_sentence_indices = self._title_based_name_retrieval()
        return self._bilateral_presence_based_name_filtering(name_candidates_2_sentence_indices)

    def _title_based_name_retrieval(self) -> Dict[str, int]:
        """ returns lowercase name candidates """
        names_2_occurrenceind = {}
        print('Procuring names...')
        for i, eng_sent in enumerate(tqdm(self.sentence_data[:, 0])):
            tokens = get_meaningful_tokens(eng_sent)
            [names_2_occurrenceind.update({name.lower(): i}) for name in filter(lambda token: token.istitle() and (len(token) > 1 or ord(token) > 255), tokens)]
        return names_2_occurrenceind

    def _bilateral_presence_based_name_filtering(self, namecandidate_2_sentenceind: Dict[str, int]) -> List[str]:
        """ returns lowercase names """
        return list(np.array(list(filter(lambda item: item[0] in map(lambda token: token.lower(), get_meaningful_tokens(self.sentence_data[item[1]][1])), list(namecandidate_2_sentenceind.items()))))[:, 0])


if __name__ == '__main__':
    dic = CustomDict({3: 5, 5: 9})
    print(dic.get(4))
