from typing import List, Tuple, Iterator
from itertools import chain
from bisect import insort
from operator import ge, le

import numpy as np

from lingularity.backend.trainers.base import TrainerBackend
from lingularity.backend.database import MongoDBClient
from lingularity.backend.data_fetching.downloading.sentence_data import fetch_sentence_data_file, language_2_ziplink
from lingularity.backend.utils.enum import ExtendedEnum


class SentenceTranslationTrainerBackend(TrainerBackend):
	def __init__(self, non_english_language: str, train_english: bool, training_mode: str, mongodb_client: MongoDBClient):
		super().__init__(non_english_language, train_english, mongodb_client)

		if self._non_english_language not in self.locally_available_languages:
			print('Downloading sentence data...')
			fetch_sentence_data_file(self._non_english_language)

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
		Lowkey = 'lowkey'
		Random = 'random'

	def _filter_sentence_data_mode_accordingly(self, sentence_data: np.ndarray, mode: str) -> np.ndarray:
		if mode == self.TrainingMode.Random.value:
			return sentence_data

		token_2_sentence_indices = self._get_token_2_sentence_indices_map(sentence_data)

		def get_limit_corresponding_sentence_indices(occurrence_limit: int, filter_mode: str) -> List[int]:
			assert filter_mode in ['max', 'min']
			operator = ge if filter_mode == 'min' else le
			return list(chain.from_iterable((indices for indices in token_2_sentence_indices.values() if operator(len(indices), occurrence_limit))))

		if mode == self.TrainingMode.VocabularyAcquisition.value:
			indices = get_limit_corresponding_sentence_indices(20, 'max')
		else:
			indices = get_limit_corresponding_sentence_indices(50, 'min')
		print('Getting corresponding sentences...')
		return sentence_data[indices]
