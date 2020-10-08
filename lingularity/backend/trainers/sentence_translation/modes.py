from typing import Union, Dict, Type, List
from itertools import chain
import operator as op
from abc import ABC, abstractmethod

import numpy as np

from lingularity.backend.trainers.base import SentenceData
from lingularity.backend.token_maps import get_token_map


class TrainingMode(ABC):
	COMPARISON_FUNCTION = Union[op.ge, op.lt, op.gt, op.le]

	def __init__(self, keyword: str, explanation: str):
		self.keyword = keyword
		self.explanation = explanation

	@abstractmethod
	def filter_sentence_data(self, sentence_data: SentenceData, language: str) -> SentenceData:
		pass

	@staticmethod
	def _filter_sentence_data(sentence_data: SentenceData, language: str, comparison_function: COMPARISON_FUNCTION) -> SentenceData:
		token_map = get_token_map(sentence_data, language, load_normalizer=False)
		token_occurrence_median = np.median(list(token_map.occurrence_map.values()))

		corresponding_tokens = (token for token, n_occurrences in token_map.occurrence_map.items() if comparison_function(n_occurrences, token_occurrence_median))
		return sentence_data[list(set(chain.from_iterable(map(token_map.get, corresponding_tokens))))]


class Random(TrainingMode):
	def __init__(self):
		super().__init__('random', 'just hit me with dem sentences')

	def filter_sentence_data(self, sentence_data: SentenceData, language: str) -> SentenceData:
		return sentence_data


class Simple(TrainingMode):
	def __init__(self):
		super().__init__('simple', 'show me sentences comprising exclusively commonly used vocabulary')

	def filter_sentence_data(self, sentence_data: SentenceData, language: str) -> SentenceData:
		return self._filter_sentence_data(sentence_data, language, comparison_function=op.ge)


class DictionExpansion(TrainingMode):
	def __init__(self):
		super().__init__('diction expansion', 'show me sentences containing rather infrequently used vocabulary')

	def filter_sentence_data(self, sentence_data: SentenceData, language: str) -> SentenceData:
		return self._filter_sentence_data(sentence_data, language, comparison_function=op.lt)


_modes = [mode() for mode in TrainingMode.__subclasses__()]
explanations: List[str] = [mode.explanation for mode in _modes]
keywords: List[str] = [mode.keyword for mode in _modes]
keyword_2_training_mode: Dict[str, Type[TrainingMode]] = {mode.keyword: mode for mode in _modes}
