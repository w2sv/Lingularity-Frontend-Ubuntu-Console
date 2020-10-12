from bisect import insort
from typing import Optional, List, Type

from lingularity.backend.database import MongoDBClient
from lingularity.backend.metadata import language_metadata
from lingularity.backend.trainers import TrainerBackend
from lingularity.backend.trainers.sentence_translation.modes import TrainingMode, keyword_2_training_mode


class SentenceTranslationTrainerBackend(TrainerBackend):
    def __init__(self, non_english_language: str, train_english: bool, mongodb_client: MongoDBClient):
        super().__init__(non_english_language, train_english, mongodb_client)

        self._training_mode: Optional[Type[TrainingMode]] = None

    def set_training_mode(self, training_mode_keyword: str):
        self._training_mode = keyword_2_training_mode[training_mode_keyword]

    def set_item_iterator(self):
        assert self._training_mode is not None

        # get sentence data, set lets go translation
        sentence_data = self._get_sentence_data()

        # get mode filtered sentence data
        filtered_sentence_data = self._training_mode.filter_sentence_data(sentence_data, self._non_english_language)

        self._set_item_iterator(training_items=filtered_sentence_data)

    @staticmethod
    def get_eligible_languages(mongodb_client: Optional[MongoDBClient] = None) -> List[str]:
        _eligible_languages = list(language_metadata.keys())
        insort(_eligible_languages, 'English')
        return _eligible_languages
