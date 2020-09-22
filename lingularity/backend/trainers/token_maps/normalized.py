import os
import pickle
from abc import ABC, abstractmethod
from typing import Optional, List, Set, Any, Iterable, Iterator, Dict, DefaultDict
from collections import defaultdict

from tqdm import tqdm
import numpy as np
import nltk
import spacy

from lingularity.backend.trainers.token_maps.base import Token2SentenceIndicesMap
from lingularity.backend.trainers.token_maps.unnormalized import UnnormalizedToken2SentenceIndices
from lingularity.backend.utils.strings import get_article_stripped_token
from lingularity.backend.utils.spacy import POS, LANGUAGE_2_CODE


class NormalizedTokenMap(ABC):
    @staticmethod
    @abstractmethod
    def is_available(language: str) -> bool:
        pass


class Stem2SentenceIndices(Token2SentenceIndicesMap, NormalizedTokenMap):
    @staticmethod
    def is_available(language: str) -> bool:
        """ Args:
                language: lowercase language """

        return language in nltk.stem.SnowballStemmer.languages

    def __init__(self, sentence_data: np.ndarray, language: str):
        """ Args:
                sentence_data
                language: lowercase language """

        super().__init__(_map=defaultdict(list))
        unnormalized_token_map = UnnormalizedToken2SentenceIndices(sentence_data, discard_proper_nouns=True)

        self._stemmer: Optional[nltk.stem.SnowballStemmer] = nltk.stem.SnowballStemmer(language)
        assert self._stemmer is not None

        print('Stemming...')
        for token, indices in tqdm(unnormalized_token_map.items(), total=unnormalized_token_map.__len__()):
            self[self._stemmer.stem(token)].extend(indices)

    def get_comprising_sentence_indices(self, entry: str) -> Optional[List[int]]:
        assert self._stemmer is not None
        return self.get(self._stemmer.stem(get_article_stripped_token(entry)))


class Lemma2SentenceIndices(Token2SentenceIndicesMap, NormalizedTokenMap):
    IGNORE_POS_TYPES = ('DET', 'PROPN', 'SYM', 'PUNCT', 'X')
    SENTENCE_TRANSLATION_MODE_MAPPING_INCLUSION_POS_TYPES = ('VERB', 'NOUN', 'ADJ', 'ADV', 'ADP')

    @staticmethod
    def is_available(language: str) -> bool:
        return language in LANGUAGE_2_CODE.keys()

    def __init__(self, sentence_data: np.ndarray, language: str):
        """ Args:
                sentence_data
                language: lowercase language """

        print('Loading model...')
        self._model = self._get_model(language)

        self.relevant_token_2_n_occurrences: DefaultDict[str, int] = defaultdict(lambda: 0)
        self._save_path = f'{os.getcwd()}/.language_data/{language.title()}/lemma_maps.pickle'

        if os.path.exists(self._save_path):
            _map, mode_relevant_token_map = pickle.load(open(self._save_path, 'rb'))

            super().__init__(_map)
            self.relevant_token_2_n_occurrences = mode_relevant_token_map

        else:
            super().__init__(_map=defaultdict(list))

            self._map_tokens(sentence_data)
            self._pickle_maps()

    @staticmethod
    def _get_model(language: str, retry=False):
        model_name = f'{LANGUAGE_2_CODE[language]}_core_{"web" if retry else "news"}_md'

        try:
            return spacy.load(model_name)
        except OSError:
            download_result = os.system(f'python -m spacy download {model_name}')
            if download_result == 256:
                return Lemma2SentenceIndices._get_model(language, retry=True)
            return spacy.load(model_name)

    def _map_tokens(self, sentence_data: np.ndarray):
        unnormalized_token_map = UnnormalizedToken2SentenceIndices(sentence_data, discard_proper_nouns=True)

        print('Creating lemma maps (will henceforth be skipped)...')
        for chunk, indices in tqdm(unnormalized_token_map.items(), total=unnormalized_token_map.__len__()):
            tokens = self._model(chunk)
            for token in tokens:
                if token.pos_ not in self.IGNORE_POS_TYPES:
                    self[token.lemma_].extend(indices)

                    if token.pos_ in self.SENTENCE_TRANSLATION_MODE_MAPPING_INCLUSION_POS_TYPES:
                        self.relevant_token_2_n_occurrences[token.lemma_] += len(indices)

    def _pickle_maps(self):
        with open(self._save_path, 'wb') as handle:
            pickle.dump((dict(self._map), dict(self.relevant_token_2_n_occurrences)), handle, protocol=pickle.HIGHEST_PROTOCOL)

    # ------------------
    # Query
    # ------------------
    def get_comprising_sentence_indices(self, entry: str) -> Optional[List[int]]:
        REMOVE_POS_TYPES = {'DET', 'PROPN', 'SYM'}
        POS_VALUES = {'NOUN': 5, 'VERB': 5,
                      'NUM': 4,
                      'AUX': 3, 'ADP': 3, 'PRON': 3,
                      'DET': 1, 'PROPN': 1, 'SYM': 1}

        def none_stripped(iterable):
            return list(filter(lambda el: el is not None, iterable))

        def intersection(nested_iterables: Iterable[Iterable[Any]]) -> Set[Any]:
            return set.intersection(*map(set, nested_iterables))

        def sentence_indices_iterator(_tokens) -> Iterator[List[int]]:
            return none_stripped((self.get(t.lemma_) for t in _tokens))

        tokens = self._model(entry)

        # remove tokens of REMOVE_POS_TYPE if tokens not solely comprised of them
        if (pos_set := set((token.pos_ for token in tokens))).intersection(REMOVE_POS_TYPES) != len(pos_set):
            tokens = list(filter(lambda token: token.pos_ not in REMOVE_POS_TYPES, tokens))

        if not (sentence_indices_list := list(sentence_indices_iterator(tokens))).__len__():
            return None

        elif (sentence_indices_list_intersection := intersection(sentence_indices_list)).__len__():
            return list(sentence_indices_list_intersection)

        else:
            pos_value_sorted_sentence_indices = set(sentence_indices_iterator(sorted(tokens, key=lambda t: POS_VALUES.get(t.pos_))))
            while len(pos_value_sorted_sentence_indices) > 1:
                pos_value_sorted_sentence_indices.pop()
                if (remaining_sentence_indices_list_intersection := intersection(
                        pos_value_sorted_sentence_indices)).__len__():
                    return list(remaining_sentence_indices_list_intersection)
            return pos_value_sorted_sentence_indices.pop()
