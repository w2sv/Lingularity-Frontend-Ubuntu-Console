from typing import *
from itertools import chain
from abc import ABC, abstractmethod
import logging
from collections import defaultdict

import numpy as np

from lingularity.backend.utils import iterables
from lingularity.backend.trainers.components import SentenceData, get_token_map
from lingularity.backend.trainers.components.token_maps import TokenMap


class TrainingMode(ABC):
	@staticmethod
	@abstractmethod
	def filter_sentence_data(sentence_data: SentenceData, language: str) -> SentenceData:
		pass

	@staticmethod
	def _token_occurrence_median(occurrence_map: TokenMap.OccurrenceMap) -> int:
		median = int(np.median(list(occurrence_map.values())))
		logging.info(f'Token occurrence median: {median}')
		return median


class Random(TrainingMode):
	@staticmethod
	def filter_sentence_data(sentence_data: SentenceData, language: str) -> SentenceData:
		return sentence_data


class Simple(TrainingMode):
	@staticmethod
	def filter_sentence_data(sentence_data: SentenceData, language: str) -> SentenceData:
		from tqdm import tqdm

		token_map = get_token_map(sentence_data, language, load_normalizer=False)
		occurrence_map = token_map.occurrence_map

		token_occurrence_mean: int = int(np.mean(list(occurrence_map.values())))
		print(token_occurrence_mean)

		sentence_index_2_comprising_tokens: Dict[int, Set[str]] = defaultdict(set)
		for token, sentence_indices in tqdm(token_map.items(), total=len(token_map)):
			for sentence_index in sentence_indices:
				sentence_index_2_comprising_tokens[sentence_index].add(token)

		sentence_index_with_comprising_occurrences: Iterator[Tuple[int, Iterator[int]]] = ((sentence_index, iterables.none_stripped(map(occurrence_map.get, comprising_tokens))) for sentence_index, comprising_tokens in sentence_index_2_comprising_tokens.items())
		sentence_indices = (sentence_index for sentence_index, comprising_occurrences in sentence_index_with_comprising_occurrences if all((occurrence >= token_occurrence_mean for occurrence in comprising_occurrences)))
		return sentence_data[list(sentence_indices)]

class DictionExpansion(TrainingMode):
	@staticmethod
	def filter_sentence_data(sentence_data: SentenceData, language: str) -> SentenceData:
		token_map = get_token_map(sentence_data, language, load_normalizer=False)
		occurrence_map = token_map.occurrence_map

		token_occurrence_median: int = TrainingMode._token_occurrence_median(occurrence_map=occurrence_map)

		tokens: Iterator[str] = (token for token, n_occurrences in occurrence_map.items() if n_occurrences <= token_occurrence_median)
		return sentence_data[list(set(chain.from_iterable(map(token_map.__getitem__, tokens))))]


if __name__ == '__main__':
	language = 'Turkish'

	sentence_data = SentenceData(language, train_english=False)
	print(len(sentence_data))

	filtered_sentence_data = Simple.filter_sentence_data(sentence_data, language)
	print(len(filtered_sentence_data))
	print(filtered_sentence_data[-30:])
