from typing import List, Tuple
from itertools import chain
from bisect import insort
from operator import ge, le

import numpy as np

from lingularity.backend.trainers import TrainerBackend
from lingularity.backend.sentence_data_fetcher import SentenceDataFetcher
from lingularity.backend.types.token_maps import Stem2SentenceIndices
from lingularity.utils.enum import ExtendedEnum


class SentenceTranslationTrainerBackend(TrainerBackend):
	_sentence_data_fetcher = SentenceDataFetcher()

	def __init__(self, non_english_language: str, train_english: bool, training_mode: str):
		super().__init__(non_english_language, train_english)

		if self._non_english_language not in self.locally_available_languages:
			self._sentence_data_fetcher.fetch_sentence_data_file(self._non_english_language)

		self._sentence_data = self._parse_sentence_data()
		self._filter_sentence_data_mode_accordingly(training_mode)
		np.random.shuffle(self._sentence_data)
		self._sentence_data_iterator = iter(self._sentence_data)

	@property
	def sentence_data_magnitude(self) -> int:
		return len(self._sentence_data)

	@staticmethod
	def get_eligible_languages() -> List[str]:
		_eligible_languages = list(SentenceTranslationTrainerBackend._sentence_data_fetcher.language_2_ziplink.keys())
		insort(_eligible_languages, 'English')
		return _eligible_languages

	# -----------------
	# .MODE
	# -----------------
	class TrainingMode(ExtendedEnum):
		VocabularyAcquisition = 'vocabulary acquisition'
		Lowkey = 'lowkey'
		Random = 'random'

	def _filter_sentence_data_mode_accordingly(self, mode: str):
		if mode == self.TrainingMode.Random.value:
			return

		stems_2_indices = Stem2SentenceIndices.from_sentence_data(self._sentence_data, self.stemmer)

		def get_limit_corresponding_sentence_indices(occurrence_limit: int, filter_mode: str) -> List[int]:
			assert filter_mode in ['max', 'min']
			operator = ge if filter_mode == 'min' else le
			return list(chain.from_iterable((indices for indices in stems_2_indices.values() if operator(len(indices), occurrence_limit))))

		if mode == self.TrainingMode.VocabularyAcquisition.value:
			indices = get_limit_corresponding_sentence_indices(20, 'max')
		else:
			indices = get_limit_corresponding_sentence_indices(50, 'min')
		print('Getting corresponding sentences...')
		self._sentence_data = self._sentence_data[indices]

	def get_sentence_pair(self) -> Tuple[str, str]:
		return next(self._sentence_data_iterator)

	def convert_names_if_possible(self, reference_sentence: str, translation: str) -> Tuple[str, str]:
		if any(default_name in reference_sentence for default_name in self.DEFAULT_NAMES) and self._names_convertible:
			return map(self._accommodate_names_of_sentence, [reference_sentence, translation])
		return reference_sentence, translation