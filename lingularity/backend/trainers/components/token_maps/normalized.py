from typing import Optional, List
from abc import ABC, abstractmethod
import os

from tqdm import tqdm
import numpy as np
import nltk

from lingularity.backend import TOKEN_MAPS_PATH
from lingularity.backend.utils import spacy as spacy_utils, data as data_utils
from lingularity.backend.trainers.components.token_maps.base import TokenMap
from lingularity.backend.trainers.components.token_maps.unnormalized import UnnormalizedTokenMap


class NormalizedTokenMap(TokenMap, ABC):
    @staticmethod
    @abstractmethod
    def is_available(language: str) -> bool:
        """ Args:
                language: titled language """

        pass


class StemMap(NormalizedTokenMap):
    @staticmethod
    def is_available(language: str) -> bool:
        return language.lower() in nltk.stem.SnowballStemmer.languages

    def __init__(self, sentence_data: np.ndarray, language: str, *args, **kwargs):
        """ Args:
                language: titled language """

        super().__init__()

        self._stemmer: nltk.stem.SnowballStemmer = nltk.stem.SnowballStemmer(language.lower())
        self._map_tokens(sentence_data)

    def _map_tokens(self, sentence_data: np.ndarray):
        unnormalized_token_map = UnnormalizedTokenMap(sentence_data, apostrophe_splitting=True)

        self._display_mapping_initialization_message()
        for token, indices in tqdm(unnormalized_token_map.items(), total=unnormalized_token_map.__len__()):
            stem = self._stemmer.stem(token)
            self[stem].extend(indices)
            self.occurrence_map[stem] += len(indices)

    def query_sentence_indices(self, vocable_entry: str) -> Optional[List[int]]:
        length_sorted_stems = list(map(self._stemmer.stem, self._get_length_sorted_meaningful_tokens(vocable_entry)))
        return self._find_best_fit_sentence_indices(length_sorted_stems)


class LemmaMap(NormalizedTokenMap):
    IGNORE_POS_TYPES = ('DET', 'PROPN', 'SYM', 'PUNCT', 'X')
    SENTENCE_TRANSLATION_MODE_MAPPING_INCLUSION_POS_TYPES = ('VERB', 'NOUN', 'ADJ', 'ADV', 'ADP')

    @staticmethod
    def is_available(language: str) -> bool:
        return language in spacy_utils.LANGUAGE_2_MODEL_IDENTIFIERS.keys()

    def __init__(self, sentence_data: np.ndarray, language: str, load_normalizer=True):
        """ Args:
                language: titled language """

        save_path = f'{TOKEN_MAPS_PATH}/{language}.pickle'
        self._model: spacy_utils.Model

        if os.path.exists(save_path):
            data, occurrence_map = data_utils.load_pickle(save_path)

            super().__init__(data=data, occurrence_map=occurrence_map)

            if load_normalizer:
                self._model = spacy_utils.load_model(language)

        else:
            super().__init__()

            self._model = spacy_utils.load_model(language)
            self._map_tokens(sentence_data)
            self._pickle_maps(save_path)

    def _map_tokens(self, sentence_data: np.ndarray):
        unnormalized_token_map = UnnormalizedTokenMap(sentence_data, apostrophe_splitting=False)

        self._display_mapping_initialization_message()
        for chunk, indices in tqdm(unnormalized_token_map.items(), total=len(unnormalized_token_map)):
            tokens = self._model(chunk)
            for token in tokens:
                if token.pos_ not in self.IGNORE_POS_TYPES:
                    self[token.lemma_].extend(indices)

                    if token.pos_ in self.SENTENCE_TRANSLATION_MODE_MAPPING_INCLUSION_POS_TYPES:
                        self.occurrence_map[token.lemma_] += len(indices)

    def _pickle_maps(self, save_path: str):
        data_utils.write_pickle(data=(dict(self._get_data()), dict(self.occurrence_map)), file_path=save_path)

    # ------------------
    # Query
    # ------------------
    def query_sentence_indices(self, vocable_entry: str) -> Optional[List[int]]:
        REMOVE_POS_TYPES = {'DET', 'PROPN', 'SYM'}
        POS_VALUES = {'NOUN': 5, 'VERB': 5, 'ADJ': 5, 'ADV': 5,
                      'NUM': 4,
                      'AUX': 3, 'ADP': 3, 'PRON': 3}

        tokens = self._model(vocable_entry)

        # remove tokens of REMOVE_POS_TYPE if tokens not solely comprised of them
        if len((pos_set := set((token.pos_ for token in tokens))).intersection(REMOVE_POS_TYPES)) != len(pos_set):
            tokens = list(filter(lambda token: token.pos_ not in REMOVE_POS_TYPES, tokens))

        pos_value_sorted_lemmas = [token.lemma_ for token in sorted(tokens, key=lambda t: POS_VALUES.get(t.pos_, 0))]
        return self._find_best_fit_sentence_indices(relevance_sorted_tokens=pos_value_sorted_lemmas)


#TODO: deficiente