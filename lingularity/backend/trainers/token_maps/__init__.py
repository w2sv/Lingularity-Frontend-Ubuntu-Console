from abc import ABC
from typing import List, Tuple, Dict, Optional, Iterator, Any, Hashable, Iterable, Union
from operator import itemgetter
from itertools import chain, groupby

from tqdm import tqdm
import numpy as np
import nltk

from lingularity.backend.utils.statistics import get_outliers
from lingularity.backend.utils.strings import get_meaningful_tokens


# TODO: include upper case tokens in proper noun query
#       distinct characters property


class CustomDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*list(filter(lambda arg: arg is not None, args)), **kwargs)

    def upsert(self, key: Hashable, value: Union[Iterable[Any], Any]):
        if len(self):
            assert hasattr(self[next(iter(self.keys()))], '__iter__')

        iterable_value = hasattr(value, '__iter__')
        if key in self:
            self[key].append(value) if not iterable_value else self[key].extend(value)
        else:
            self[key] = [value] if not iterable_value else value


class Token2Indices(CustomDict, ABC):
    def __init__(self, token_map: Optional[Dict] = None):
        super().__init__(token_map)

        self._n_occurrences_2_tokens: Optional[CustomDict] = None

    @property
    def distinct_characters(self) -> List[str]:
        return sorted(set(chain.from_iterable(map(list, list(self.keys())))))

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
    def occurrences_2_tokens(self) -> CustomDict:
        if self._n_occurrences_2_tokens is None:
            self._n_occurrences_2_tokens = CustomDict()
            for token, indices in self.items():
                self._n_occurrences_2_tokens.upsert(len(indices), token)
        return self._n_occurrences_2_tokens

    # ----------------
    # OCCURRENCE OUTLIER BASED, not used
    # ----------------
    def _get_occurrence_outlier_corresponding_tokens(self, occurrence_outliers: List[int]) -> Iterator[str]:
        return chain.from_iterable(itemgetter(*occurrence_outliers)(self.occurrences_2_tokens))

    def pop_positive_occurrence_outliers(self, iqr_coefficient: float = 0.2):
        occurrence_outliers = get_outliers(list(self.occurrences_2_tokens.keys()), positive=True, iqr_coefficient=iqr_coefficient)
        corresponding_tokens = self._get_occurrence_outlier_corresponding_tokens(occurrence_outliers)
        [self.pop(outlier_token) for outlier_token in corresponding_tokens]

    def get_negative_occurrence_outliers(self, iqr_coefficient: float = 0):  # -> Token2IndicesBase
        occurrence_outliers = get_outliers(list(self.occurrences_2_tokens.keys()), positive=False, iqr_coefficient=iqr_coefficient)
        corresponding_tokens = self._get_occurrence_outlier_corresponding_tokens(occurrence_outliers)
        return {token: self[token] for token in corresponding_tokens}


class RawToken2SentenceIndices(Token2Indices):
    """ dict with
            keys: distinct lowercase delimiter-split, punctuation-stripped foreign language _vocable_entries tokens
                excluding numbers
            values: lists of sentence indices in which occurring """

    def __init__(self, sentence_data: np.ndarray, language: Optional[str] = None):
        super().__init__()

        self._sentence_data = sentence_data

        print(f'Mapping {language + " " if language else ""}tokens...')
        for i, sentence in enumerate(tqdm(self._sentence_data[:, 1])):
            # split, discard impertinent characters, lower all
            tokens = (token.lower() for token in get_meaningful_tokens(sentence))
            for token in tokens:
                if not len(token) or any(i.isdigit() for i in token):
                    continue
                self.upsert(token, i)


class Stem2SentenceIndices(Token2Indices):
    def __init__(self, raw_token_map: RawToken2SentenceIndices, stemmer: Optional[nltk.stem.SnowballStemmer]):
        super().__init__()

        self._raw_token_map: RawToken2SentenceIndices = raw_token_map
        self._stemmer: Optional[nltk.stem.SnowballStemmer] = stemmer
        self._proper_nouns = self._get_proper_nouns()

        starting_letter_grouped_names: Dict[str, List[str]] = {k: list(v) for k, v in groupby(sorted(self._proper_nouns), lambda name: name[0])}

        print('Discarding proper nouns, stemming...' if self._stemmer is not None else 'Discarding proper nouns...')
        for token, indices in tqdm(list(self._raw_token_map.items())):
            if starting_letter_grouped_names.get(token[0]) is not None and token in starting_letter_grouped_names[token[0]]:
                continue
            if self._stemmer is not None:
                token = self._stemmer.stem(token)
            self.upsert(token, indices)

    @classmethod
    def from_sentence_data(cls, sentence_data: np.ndarray, stemmer: Optional[nltk.stem.SnowballStemmer]):
        return cls(RawToken2SentenceIndices(sentence_data), stemmer)

    def __getattr__(self, attr):
        """ forwarding _sentence_data calls """

        return getattr(self._raw_token_map, attr)

    # ----------------
    # PROPER NOUN QUERY
    # ----------------
    def _get_proper_nouns(self) -> List[str]:
        name_candidates_2_sentence_indices = self._title_based_proper_noun_retrieval()
        return list(self._bilateral_presence_based_proper_noun_filtering(name_candidates_2_sentence_indices))

    def _title_based_proper_noun_retrieval(self) -> Dict[str, int]:
        """ returns lowercase name candidates """

        names_2_sentenceindex = {}
        print('Procuring proper nouns...')
        for i, eng_sent in enumerate(tqdm(self._sentence_data[:, 0])):
            tokens = get_meaningful_tokens(eng_sent)
            [names_2_sentenceindex.update({name.lower(): i}) for name in filter(lambda token: token.istitle() and (len(token) > 1 or ord(token) > 255), tokens)]
        return names_2_sentenceindex

    def _bilateral_presence_based_proper_noun_filtering(self, namecandidate_2_sentenceind: Dict[str, int]) -> List[str]:
        """ returns lowercase names """

        return list(np.asarray(list(filter(lambda item: item[0] in map(lambda token: token.lower(), get_meaningful_tokens(self._sentence_data[item[1]][1])), list(namecandidate_2_sentenceind.items()))))[:, 0])
