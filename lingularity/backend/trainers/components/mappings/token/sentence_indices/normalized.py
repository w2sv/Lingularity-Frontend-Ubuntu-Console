from typing import Optional, List, Iterator, Tuple, Union
from abc import ABC, abstractmethod
import os

import nltk
from spacy.tokens import Token

from lingularity.backend import TOKEN_MAPS_PATH
from lingularity.backend.utils import spacy as spacy_utils, data as data_utils, strings
from lingularity.backend.trainers.components.mappings.token.sentence_indices.base import SegmentSentenceIndicesMap


class NormalizedTokenSentenceIndicesMap(SegmentSentenceIndicesMap, ABC):
    @staticmethod
    @abstractmethod
    def is_available(language: str) -> bool:
        """ Args:
                language: titled language """

        pass

    @abstractmethod
    def _tokenize(self, text: str) -> List[Union[Token, str]]:
        pass

    @abstractmethod
    def _normalize(self, tokens: List[str]) -> List[str]:
        pass


class StemSentenceIndicesMap(NormalizedTokenSentenceIndicesMap):
    @staticmethod
    def is_available(language: str) -> bool:
        return language.lower() in nltk.stem.SnowballStemmer.languages

    def __init__(self, language: str, create=False, *args, **kwargs):
        """ Args:
                language: titled language """

        super().__init__(language, create=create)

        self._stemmer: nltk.stem.SnowballStemmer = nltk.stem.SnowballStemmer(language.lower())

    def tokenize(self, sentence: str) -> List[str]:
        return self._normalize(self._tokenize(sentence))

    def _tokenize(self, text: str) -> List[str]:
        return strings.get_meaningful_tokens(text=text, apostrophe_splitting=True)

    def _normalize(self, tokens: List[str]) -> List[str]:
        return list(map(self._stemmer.stem, tokens))

    def query_sentence_indices(self, vocable_entry: str) -> Optional[List[int]]:
        length_sorted_stems = list(map(self._stemmer.stem, self._get_length_sorted_meaningful_tokens(vocable_entry)))
        return self._find_best_fit_sentence_indices(length_sorted_stems)


class LemmaSentenceIndicesMap(NormalizedTokenSentenceIndicesMap):
    _IGNORE_POS_TYPES = ('DET', 'PROPN', 'SYM', 'PUNCT', 'X', 'PART')

    @staticmethod
    def is_available(language: str) -> bool:
        return language in spacy_utils.LANGUAGE_2_MODEL_IDENTIFIERS.keys()

    def __init__(self, language: str, create=False, load_normalizer=True):
        """ Args:
                language: titled language """

        super().__init__(language, create=create)

        self._model: spacy_utils.Model

        if load_normalizer:
            self._model = spacy_utils.load_model(language)

    def tokenize_with_pos_tags(self, sentence: str) -> List[Tuple[str, str]]:
        filtered_tokens = self._filter_tokens(self._tokenize(strings.strip_special_characters(string=sentence)))
        return list(map(lambda token: (token.lemma_, token.pos_), filtered_tokens))

    def tokenize(self, sentence: str) -> List[str]:
        return self._normalize(self._filter_tokens(self._tokenize(sentence)))

    def _normalize(self, tokens: List[Token]) -> List[str]:
        return [token.lemma_ for token in tokens]

    def _filter_tokens(self, tokens: List[Token]) -> List[Token]:
        return list(filter(lambda token: token.pos_ not in self._IGNORE_POS_TYPES, tokens))

    def _tokenize(self, text: str) -> List[Token]:
        return self._model(text)

    # ------------------
    # Query
    # ------------------
    def query_sentence_indices(self, vocable_entry: str) -> Optional[List[int]]:
        REMOVE_POS_TYPES = {'DET', 'PROPN', 'SYM'}

        tokens = self._tokenize(vocable_entry)

        # remove tokens of REMOVE_POS_TYPE if tokens not solely comprised of them
        if len((pos_set := set((token.pos_ for token in tokens))).intersection(REMOVE_POS_TYPES)) != len(pos_set):
            tokens = list(filter(lambda token: token.pos_ not in REMOVE_POS_TYPES, tokens))

        pos_value_sorted_lemmas = [token.lemma_ for token in sorted(tokens, key=lambda t: spacy_utils.POS_VALUES.get(t.pos_, spacy_utils.PosValue.Null).value)]
        return self._find_best_fit_sentence_indices(relevance_sorted_tokens=pos_value_sorted_lemmas)


if __name__ == '__main__':
    _map = LemmaSentenceIndicesMap('Italian')
    print(list(_map.keys()))
    print(len(_map))
