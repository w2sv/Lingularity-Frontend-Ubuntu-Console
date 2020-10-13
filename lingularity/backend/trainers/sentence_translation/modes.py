from typing import Callable
from itertools import chain
import operator as op
from abc import ABC, abstractmethod

import numpy as np

from lingularity.backend.trainers.base import SentenceData
from lingularity.backend.components.token_maps import get_token_map


class TrainingMode(ABC):
	@staticmethod
	@abstractmethod
	def filter_sentence_data(sentence_data: SentenceData, language: str) -> SentenceData:
		pass

	@staticmethod
	def _filter_sentence_data(sentence_data: SentenceData, language: str, comparison_function: Callable[[int, int], bool]) -> SentenceData:
		token_map = get_token_map(sentence_data, language, load_normalizer=False)
		token_occurrence_median = int(np.median(list(token_map.occurrence_map.values())))

		mode_corresponding_tokens = (token for token, n_occurrences in token_map.occurrence_map.items() if comparison_function(n_occurrences, token_occurrence_median))
		return sentence_data[list(set(chain.from_iterable(map(token_map.get, mode_corresponding_tokens))))]  # type: ignore


class Random(TrainingMode):
	@staticmethod
	def filter_sentence_data(sentence_data: SentenceData, language: str) -> SentenceData:
		return sentence_data


class Simple(TrainingMode):
	@staticmethod
	def filter_sentence_data(sentence_data: SentenceData, language: str) -> SentenceData:
		return TrainingMode._filter_sentence_data(sentence_data, language, comparison_function=op.ge)


class DictionExpansion(TrainingMode):
	@staticmethod
	def filter_sentence_data(sentence_data: SentenceData, language: str) -> SentenceData:
		return TrainingMode._filter_sentence_data(sentence_data, language, comparison_function=op.lt)
