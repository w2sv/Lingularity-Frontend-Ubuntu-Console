from typing import Optional, List, Type
from bisect import insort

from lingularity.backend.database import MongoDBClient
from lingularity.backend.metadata import language_metadata
from lingularity.backend.trainers import TrainerBackend
from lingularity.backend.resources import strings as string_resources
from .modes import TrainingMode


class SentenceTranslationTrainerBackend(TrainerBackend):
    def __init__(self, non_english_language: str, train_english: bool, mongodb_client: MongoDBClient):
        super().__init__(non_english_language, train_english, mongodb_client)

        self._training_mode: Optional[Type[TrainingMode]] = None

    def set_training_mode(self, training_mode: Type[TrainingMode]):
        assert self._training_mode is None, "training mode shan't be reassigned"
        self._training_mode = training_mode

    def set_item_iterator(self):
        assert self._training_mode is not None

        # get sentence data
        sentence_data = self._get_sentence_data()

        # get mode filtered sentence data
        filtered_sentence_data = self._training_mode.filter_sentence_data(sentence_data, self._non_english_language)

        self._set_item_iterator(training_items=filtered_sentence_data)

    @staticmethod
    def get_eligible_languages(mongodb_client: Optional[MongoDBClient] = None) -> List[str]:
        _eligible_languages = list(language_metadata.keys())
        insort(_eligible_languages, string_resources.ENGLISH)
        return _eligible_languages
