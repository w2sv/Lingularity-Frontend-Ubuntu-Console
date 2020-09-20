import os
import pickle
from abc import abstractmethod
from typing import Optional, List

from tqdm import tqdm
import numpy as np
import nltk
import spacy

from lingularity.backend.trainers.token_maps.base import Token2SentenceIndicesMap
from lingularity.backend.trainers.token_maps.unnormalized import UnnormalizedToken2SentenceIndices


class NormalizedTokenMap(Token2SentenceIndicesMap):
    @staticmethod
    @abstractmethod
    def is_available(language: str) -> bool:
        pass

    def __init__(self, sentence_data: np.ndarray):
        super().__init__()
        self._unnormalized_token_map = UnnormalizedToken2SentenceIndices(sentence_data, discard_proper_nouns=True)


class Stem2SentenceIndices(NormalizedTokenMap):
    @staticmethod
    def is_available(language: str) -> bool:
        """ Args:
                language: lowercase language """

        return language in nltk.stem.SnowballStemmer.languages

    def __init__(self, sentence_data: np.ndarray, language: str):
        """ Args:
                sentence_data
                language: lowercase language """

        super().__init__(sentence_data)

        self._stemmer: Optional[nltk.stem.SnowballStemmer] = nltk.stem.SnowballStemmer(language)
        assert self._stemmer is not None, 'stemming feasibility to be asserted before instantiation'

        print('Stemming...')
        for token, indices in self._unnormalized_token_map.items():
            self.upsert(self._stemmer.stem(token), indices)

    def get_comprising_sentence_indices(self, article_stripped_token: str) -> Optional[List[int]]:
        return self.get(self._stemmer.stem(article_stripped_token))


class Lemma2SentenceIndices(NormalizedTokenMap):
    _LANGUAGE_2_CODE = {'chinese': 'zh', 'danish': 'da', 'dutch': 'nl', 'english': 'en',
                        'french': 'fr', 'german': 'de', 'greek': 'el', 'italian': 'it',
                        'japanese': 'ja', 'lithuanian': 'lt', 'norwegian': 'nb', 'polish': 'pl',
                        'portuguese': 'pt', 'romanian': 'ro', 'spanish': 'es'}

    model = None

    @staticmethod
    def is_available(language: str) -> bool:
        return language in Lemma2SentenceIndices._LANGUAGE_2_CODE.keys()

    @staticmethod
    def exists(language: str) -> bool:
        return os.path.exists(Lemma2SentenceIndices._file_path(language))

    @classmethod
    def from_file(cls, language: str):
        Lemma2SentenceIndices.model = Lemma2SentenceIndices._get_model(language)

        with open(Lemma2SentenceIndices._file_path(language), 'rb') as handle:
            return pickle.load(handle)

    @staticmethod
    def _file_path(language) -> str:
        return f'{os.getcwd()}/language_data/{language.title()}/lemma_2_sentence_indices.pickle'

    def __init__(self, sentence_data: np.ndarray, language: str):
        """ Args:
                sentence_data
                language: lowercase language """

        super().__init__(sentence_data)

        self.model = self._get_model(language)

        print('Lemmatizing...')
        for token, indices in tqdm(list(self._unnormalized_token_map.items())):
            lemma = self._lemmatize(token)
            self.upsert(lemma, indices)

        self._pickle(language)

    def _lemmatize(self, token: str) -> str:
        return self.model(token)[0].lemma_

    @staticmethod
    def _get_model(language: str):
        model_name = f'{Lemma2SentenceIndices._LANGUAGE_2_CODE[language]}_core_news_md'

        try:
            return spacy.load(model_name)
        except OSError:
            os.system(f'python -m spacy download {model_name}')
            return spacy.load(model_name)

    def _pickle(self, language: str):
        with open(self._file_path(language), 'wb') as handle:
            pickle.dump(self, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # ------------------
    # Query
    # ------------------
    def get_comprising_sentence_indices(self, article_stripped_token: str) -> Optional[List[int]]:
        return self.get(self._lemmatize(article_stripped_token))
