import os
import pickle
from abc import ABC, abstractmethod
from typing import Optional, List

from tqdm import tqdm
import numpy as np
import nltk
import spacy

from lingularity.backend.trainers.token_maps.base import TokenMap
from lingularity.backend.trainers.token_maps.unnormalized import UnnormalizedTokenMap
from lingularity.backend.utils.spacy import LANGUAGE_2_CODE


class NormalizedTokenMap(TokenMap, ABC):
    def __init__(self):
        super().__init__()

    @staticmethod
    @abstractmethod
    def is_available(language: str) -> bool:
        """ Args:
                language: lowercase language """

        pass


class StemMap(NormalizedTokenMap):
    @staticmethod
    def is_available(language: str) -> bool:
        return language in nltk.stem.SnowballStemmer.languages

    def __init__(self, sentence_data: np.ndarray, language: str, *args):
        """ Args:
                language: lowercase language """

        super().__init__()

        self._stemmer: Optional[nltk.stem.SnowballStemmer] = nltk.stem.SnowballStemmer(language)
        self._map_tokens(sentence_data)

    def _map_tokens(self, sentence_data: np.ndarray):
        assert self._stemmer is not None

        unnormalized_token_map = UnnormalizedTokenMap(sentence_data)

        self._output_mapping_initialization_message()
        for token, indices in tqdm(unnormalized_token_map.items(), total=unnormalized_token_map.__len__()):
            stem = self._stemmer.stem(token)
            self[stem].extend(indices)
            self.occurrence_map[stem] += len(indices)

    def get_comprising_sentence_indices(self, vocable_entry: str) -> Optional[List[int]]:
        assert self._stemmer is not None

        length_sorted_stems = list(map(self._stemmer.stem, self._get_length_sorted_meaningful_tokens(vocable_entry)))
        return self._find_best_fit_sentence_indices(length_sorted_stems)


class LemmaMap(NormalizedTokenMap):
    IGNORE_POS_TYPES = ('DET', 'PROPN', 'SYM', 'PUNCT', 'X')
    SENTENCE_TRANSLATION_MODE_MAPPING_INCLUSION_POS_TYPES = ('VERB', 'NOUN', 'ADJ', 'ADV', 'ADP')

    @staticmethod
    def is_available(language: str) -> bool:
        return language in LANGUAGE_2_CODE.keys()

    def __init__(self, sentence_data: np.ndarray, language: str, load_normalizer=True):
        """ Args:
                language: lowercase language """

        super().__init__()

        self._save_path = f'{os.getcwd()}/.language_data/{language.title()}/lemma_maps.pickle'
        self._model = None

        if os.path.exists(self._save_path):
            self._map, self.occurrence_map = pickle.load(open(self._save_path, 'rb'))
            if load_normalizer:
                self._model = self._get_model(language)

        else:
            self._model = self._get_model(language)
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
                return LemmaMap._get_model(language, retry=True)
            print('Loading model...')
            return spacy.load(model_name)

    def _map_tokens(self, sentence_data: np.ndarray):
        assert self._model is not None

        unnormalized_token_map = UnnormalizedTokenMap(sentence_data)

        self._output_mapping_initialization_message()
        for chunk, indices in tqdm(unnormalized_token_map.items(), total=unnormalized_token_map.__len__()):
            tokens = self._model(chunk)
            for token in tokens:
                if token.pos_ not in self.IGNORE_POS_TYPES:
                    self[token.lemma_].extend(indices)

                    if token.pos_ in self.SENTENCE_TRANSLATION_MODE_MAPPING_INCLUSION_POS_TYPES:
                        self.occurrence_map[token.lemma_] += len(indices)

    def _pickle_maps(self):
        with open(self._save_path, 'wb') as handle:
            pickle.dump((dict(self._map), dict(self.occurrence_map)), handle, protocol=pickle.HIGHEST_PROTOCOL)

    # ------------------
    # Query
    # ------------------
    def get_comprising_sentence_indices(self, vocable_entry: str) -> Optional[List[int]]:
        REMOVE_POS_TYPES = {'DET', 'PROPN', 'SYM'}
        POS_VALUES = {'NOUN': 5, 'VERB': 5, 'ADJ': 5, 'ADV': 5,
                      'NUM': 4,
                      'AUX': 3, 'ADP': 3, 'PRON': 3}

        assert self._model is not None
        tokens = self._model(vocable_entry)

        # remove tokens of REMOVE_POS_TYPE if tokens not solely comprised of them
        if len((pos_set := set((token.pos_ for token in tokens))).intersection(REMOVE_POS_TYPES)) != len(pos_set):
            tokens = list(filter(lambda token: token.pos_ not in REMOVE_POS_TYPES, tokens))

        pos_value_sorted_lemmas = [token.lemma_ for token in sorted(tokens, key=lambda t: POS_VALUES.get(t.pos_, 0))]
        return self._find_best_fit_sentence_indices(relevance_sorted_tokens=pos_value_sorted_lemmas)
