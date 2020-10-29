from typing import Optional, Type

from lingularity.backend.trainers import TrainerBackend
from .modes import TrainingMode
from .text_to_speech import TextToSpeech


class SentenceTranslationTrainerBackend(TrainerBackend):
    def __init__(self, non_english_language: str, train_english: bool):
        super().__init__(non_english_language, train_english)

        TextToSpeech(self.language)
        self._training_mode: Optional[Type[TrainingMode]] = None

    @property
    def training_mode(self) -> Optional[Type[TrainingMode]]:
        return self._training_mode

    @training_mode.setter
    def training_mode(self, mode: Type[TrainingMode]):
        assert self._training_mode is None, "training mode shan't be reassigned"
        self._training_mode = mode

    def set_item_iterator(self):
        assert self._training_mode is not None

        # get sentence data
        sentence_data = self._get_sentence_data()

        # get mode filtered sentence data
        filtered_sentence_data = self._training_mode.filter_sentence_data(sentence_data, self._non_english_language)

        self._set_item_iterator(training_items=filtered_sentence_data)
