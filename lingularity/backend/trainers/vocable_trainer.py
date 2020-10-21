from typing import List, Optional, Sequence
from itertools import repeat, starmap
from aenum import NoAliasEnum
from functools import cached_property

import unidecode
import numpy as np

from lingularity.backend.trainers.base import TrainerBackend
from lingularity.backend.database import MongoDBClient
from lingularity.backend.utils.strings import get_article_stripped_noun
from lingularity.backend.components import (
    SentenceData,
    VocableEntry,
    TokenMap,
    get_token_map
)


class VocableTrainerBackend(TrainerBackend):
    def __init__(self, non_english_language: str, train_english: bool, mongodb_client: MongoDBClient):
        super().__init__(non_english_language, train_english, mongodb_client)

        self._training_items: Optional[List[VocableEntry]] = None
        self._sentence_data: SentenceData = self._get_sentence_data()
        self._token_2_sentence_indices: TokenMap = get_token_map(self._sentence_data, self.language, load_normalizer=True)

    @staticmethod
    def get_eligible_languages(mongodb_client: Optional[MongoDBClient]) -> List[str]:
        assert mongodb_client is not None

        return mongodb_client.query_vocabulary_possessing_languages()

    def set_item_iterator(self):
        self._training_items = self._get_imperfect_vocable_entries()
        self._set_item_iterator(self._training_items)

    def _get_imperfect_vocable_entries(self) -> List[VocableEntry]:
        entire_vocabulary = starmap(VocableEntry, zip(self.mongodb_client.query_vocabulary_data(), repeat(self._train_english)))
        return list(filter(lambda vocable_entry: not vocable_entry.is_perfected, entire_vocabulary))

    # ---------------
    # Pre Training
    # ---------------
    @cached_property
    def new_vocable_entries(self) -> List[VocableEntry]:
        assert self._training_items is not None

        return list(filter(lambda entry: entry.is_new, self._training_items))

    # ---------------
    # Training
    # ---------------
    def related_sentence_pairs(self, entry: str, n: int) -> Sequence[Sequence[str]]:
        if (sentence_indices := self._token_2_sentence_indices.query_sentence_indices(entry)) is None:
            return []

        sentence_indices = np.asarray(sentence_indices)
        np.random.shuffle(sentence_indices)
        return self._sentence_data[sentence_indices[:n]]

    # ---------------
    # .Evaluation
    # ---------------
    class ResponseEvaluation(NoAliasEnum):
        NoResponse = 0.0
        Wrong = 0.0
        MissingArticle = 0.5
        WrongArticle = 0.5
        AlmostCorrect = 0.5
        AccentError = 0.75
        Correct = 1.0

    @staticmethod
    def response_evaluation(response: str, translation: str) -> ResponseEvaluation:
        response = response.strip(' ')

        if not len(response):
            return VocableTrainerBackend.ResponseEvaluation.NoResponse
        elif response == translation:
            return VocableTrainerBackend.ResponseEvaluation.Correct
        elif response == unidecode.unidecode(translation):
            return VocableTrainerBackend.ResponseEvaluation.AccentError
        elif VocableTrainerBackend._n_char_deviations(response, translation) <= VocableTrainerBackend._n_tolerable_char_deviations(translation):
            return VocableTrainerBackend.ResponseEvaluation.AlmostCorrect
        elif VocableTrainerBackend._article_missing(response, translation):
            return VocableTrainerBackend.ResponseEvaluation.MissingArticle
        elif VocableTrainerBackend._wrong_article(response, translation):
            return VocableTrainerBackend.ResponseEvaluation.WrongArticle
        return VocableTrainerBackend.ResponseEvaluation.Wrong

    @staticmethod
    def _wrong_article(response: str, translation: str) -> bool:
        return len((contained_nouns := set(map(get_article_stripped_noun, [response, translation])))) == 1 and next(iter(contained_nouns))

    @staticmethod
    def _article_missing(response: str, translation: str) -> bool:
        return get_article_stripped_noun(translation) == response

    @staticmethod
    def _n_tolerable_char_deviations(translation: str) -> int:
        N_ALLOWED_NON_WHITESPACE_CHARS_PER_DEVIATION = 4

        return len(translation.replace(' ', '')) // N_ALLOWED_NON_WHITESPACE_CHARS_PER_DEVIATION

    @staticmethod
    def _n_char_deviations(response, translation) -> int:
        n_deviations = 0

        modified_response = response
        for i in range(len(translation)):
            try:
                if modified_response[i] != translation[i]:
                    n_deviations += 1

                    if len(modified_response) < len(translation):
                        modified_response = modified_response[:i] + ' ' + modified_response[i:]

                    elif len(modified_response) > len(translation):
                        modified_response = modified_response[:i] + modified_response[i+1:]
            except IndexError:
                n_deviations += len(translation) - len(response)
                break

        return n_deviations


if __name__ == '__main__':
    print(VocableTrainerBackend.response_evaluation(response='baretto', translation='il baretto'))
    print(VocableTrainerBackend.response_evaluation(response='la baretto', translation='il baretto'))