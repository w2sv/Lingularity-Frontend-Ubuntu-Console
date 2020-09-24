from typing import List, Tuple, Iterator
from itertools import chain
from bisect import insort
import operator

import numpy as np

from lingularity.backend.trainers.base import TrainerBackend
from lingularity.backend.database import MongoDBClient
from lingularity.backend.data_fetching.downloading.sentence_data import fetch_sentence_data, language_2_ziplink
from lingularity.backend.utils.enum import ExtendedEnum


class SentenceTranslationTrainerBackend(TrainerBackend):
	def __init__(self, non_english_language: str, train_english: bool, training_mode: str, mongodb_client: MongoDBClient):
		super().__init__(non_english_language, train_english, mongodb_client)

		if self._non_english_language not in self.locally_available_languages:
			print('Downloading sentence data...')
			fetch_sentence_data(self._non_english_language)

		sentence_data, self.lets_go_translation = self._process_sentence_data_file()

		filtered_sentence_data = self._filter_sentence_data_mode_accordingly(sentence_data, training_mode)
		self.sentence_data_magnitude = len(filtered_sentence_data)
		self._item_iterator: Iterator[Tuple[str, str]] = self._get_item_iterator(filtered_sentence_data)

	@staticmethod
	def get_eligible_languages() -> List[str]:
		assert language_2_ziplink is not None

		_eligible_languages = list(language_2_ziplink.keys())
		insort(_eligible_languages, 'English')
		return _eligible_languages

	# -----------------
	# .Mode
	# -----------------
	class TrainingMode(ExtendedEnum):
		VocabularyAcquisition = 'vocabulary acquisition'
		Simple = 'simple'
		Random = 'random'

	def _filter_sentence_data_mode_accordingly(self, sentence_data: np.ndarray, mode: str) -> np.ndarray:
		if mode == self.TrainingMode.Random.value:
			return sentence_data

		token_map = self._get_token_map(sentence_data)
		token_occurrence_median = np.median(list(token_map.occurrence_map.values()))

		def get_sentence_indices(comparison) -> List[int]:
			corresponding_tokens = (token for token, n_occurrences in token_map.occurrence_map.items() if comparison(n_occurrences, token_occurrence_median))
			return list(set(chain.from_iterable(map(token_map.get, corresponding_tokens))))

		if mode == self.TrainingMode.VocabularyAcquisition.value:
			return sentence_data[get_sentence_indices(operator.lt)]

		elif mode == self.TrainingMode.Simple.value:
			return sentence_data[get_sentence_indices(operator.ge)]
