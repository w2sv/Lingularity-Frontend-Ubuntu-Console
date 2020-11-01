from typing import *
from itertools import chain
from abc import ABC, abstractmethod
import logging
from collections import defaultdict

import numpy as np

from lingularity.backend.utils import iterables
from lingularity.backend.trainers.components import (
	SentenceData,
	TokenSentenceIndicesMap,
	get_token_sentence_indices_map,
	TokenOccurrencesMap
)


class TrainingMode(ABC):
	@staticmethod
	@abstractmethod
	def filter_sentence_data(sentence_data: SentenceData, language: str) -> SentenceData:
		pass

	@staticmethod
	def _token_occurrence_median(occurrence_map: TokenOccurrencesMap) -> int:
		median = int(np.median(list(occurrence_map.values())))
		logging.info(f'Token occurrence median: {median}')
		return median

	@staticmethod
	def _get_token_maps(language: str) -> Tuple[TokenSentenceIndicesMap, TokenOccurrencesMap]:
		return get_token_sentence_indices_map(language, load_normalizer=False), TokenOccurrencesMap(language)


class Random(TrainingMode):
	@staticmethod
	def filter_sentence_data(sentence_data: SentenceData, language: str) -> SentenceData:
		return sentence_data


class Simple(TrainingMode):
	@staticmethod
	def filter_sentence_data(sentence_data: SentenceData, language: str) -> SentenceData:
		from tqdm import tqdm

		token_sentence_indices_map, token_occurrences_map = TrainingMode._get_token_maps(language)

		token_occurrence_mean: int = int(np.mean(list(token_occurrences_map.values())))
		print(token_occurrence_mean)

		sentence_index_2_comprising_tokens: Dict[int, Set[str]] = defaultdict(set)
		for token, sentence_indices in tqdm(token_sentence_indices_map.items(), total=len(token_sentence_indices_map)):
			for sentence_index in sentence_indices:
				sentence_index_2_comprising_tokens[sentence_index].add(token)

		sentence_index_with_comprising_occurrences: Iterator[Tuple[int, Iterator[int]]] = ((sentence_index, iterables.none_stripped(map(token_occurrences_map.get, comprising_tokens))) for sentence_index, comprising_tokens in sentence_index_2_comprising_tokens.items())
		sentence_indices = (sentence_index for sentence_index, comprising_occurrences in sentence_index_with_comprising_occurrences if all((occurrence >= token_occurrence_mean for occurrence in comprising_occurrences)))
		return sentence_data[list(sentence_indices)]

class DictionExpansion(TrainingMode):
	@staticmethod
	def filter_sentence_data(sentence_data: SentenceData, language: str) -> SentenceData:
		token_sentence_indices_map, token_occurrences_map = TrainingMode._get_token_maps(language)

		token_occurrence_median: int = TrainingMode._token_occurrence_median(occurrence_map=token_occurrences_map)

		tokens: Iterator[str] = (token for token, n_occurrences in token_occurrences_map.items() if n_occurrences <= token_occurrence_median)
		return sentence_data[list(set(chain.from_iterable(map(token_sentence_indices_map.__getitem__, tokens))))]


if __name__ == '__main__':
	language = 'Turkish'

	sentence_data = SentenceData(language, train_english=False)
	print(len(sentence_data))

	filtered_sentence_data = Simple.filter_sentence_data(sentence_data, language)
	print(len(filtered_sentence_data))
	print(filtered_sentence_data[-30:])
