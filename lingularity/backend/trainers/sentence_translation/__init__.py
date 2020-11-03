from lingularity.backend.trainers.base import TrainerBackend
from .modes import SentenceDataFilter
from .text_to_speech import TextToSpeech


class SentenceTranslationTrainerBackend(TrainerBackend):
    def __init__(self, non_english_language: str, train_english: bool):
        super().__init__(non_english_language, train_english)

        TextToSpeech(self.language)
        self._sentence_data_filter: SentenceDataFilter = None  # type: ignore

    @property
    def sentence_data_filter(self) -> SentenceDataFilter:
        return self._sentence_data_filter

    @sentence_data_filter.setter
    def sentence_data_filter(self, _filter: SentenceDataFilter):
        self._sentence_data_filter = _filter

    def set_item_iterator(self):
        # get sentence data
        sentence_data = self._get_sentence_data()

        # get mode filtered sentence data
        filtered_sentence_data = self._sentence_data_filter(sentence_data, self._non_english_language)

        self._set_item_iterator(training_items=filtered_sentence_data)
