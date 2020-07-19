import sys
import os
import time
from typing import List, Optional, Tuple
from itertools import groupby, chain
from bisect import insort
from operator import ge, le

import numpy as np
from pynput.keyboard import Controller as KeyboardController

from lingularity.trainers import Trainer
from lingularity.webpage_interaction import ContentRetriever
from lingularity.types.token_maps import Stem2SentenceIndices
from lingularity.database import MongoDBClient
from lingularity.utils.enum import ExtendedEnum
from lingularity.utils.output_manipulation import clear_screen, erase_lines
from lingularity.utils.input_resolution import resolve_input, recurse_on_invalid_input


class SentenceTranslationTrainer(Trainer):
	def __init__(self, database_client: MongoDBClient):
		self._content_retriever = ContentRetriever()

		super().__init__(database_client)


	def run(self):
		if self._non_english_language not in self.locally_available_languages:
			self._download_and_process_zip_file()

		self._sentence_data = self._parse_sentence_data()

		if (mode_selection := self._select_mode()) != self.Mode.Random.value:
			self._filter_sentences_mode_accordingly(mode_selection)

		self._display_pre_training_instructions()
		self._train()

		self._insert_session_statistics_into_database()
		if self._n_trained_items > 5:
			self._plot_training_history()

	def _download_and_process_zip_file(self):
		zip_file_link = self._content_retriever.download_zipfile(self._non_english_language)
		self._content_retriever.unzip_file(zip_file_link)

	# ---------------
	# INITIALIZATION
	# ---------------
	def _select_language(self) -> str:
		if self._content_retriever.languages_2_ziplinks is None:
			print('Trying to connect to webpage...')
			self._content_retriever.get_language_ziplink_dict()
		assert self._content_retriever.languages_2_ziplinks is not None
		sucessfully_retrieved = bool(len(self._content_retriever.languages_2_ziplinks))
		eligible_languages = list(self._content_retriever.languages_2_ziplinks.keys()) if sucessfully_retrieved else os.listdir(self.BASE_LANGUAGE_DATA_PATH)
		if 'English' not in eligible_languages:
			insort(eligible_languages, 'English')

		clear_screen()
		if len(eligible_languages) == 1:  # solely artificially appended english
			print('Please establish an internet connection in order to download sentence data.')
			print('Terminating program.')
			time.sleep(3)
			sys.exit(0)

		elif not sucessfully_retrieved:
			print("Couldn't establish a connection")

		starting_letter_grouped = groupby(eligible_languages, lambda x: x[0])
		print('Eligible languages: '.upper())
		for _, values in starting_letter_grouped:
			print(', '.join(list(values)))

		selection = resolve_input(input('\nSelect language: \n').title(), eligible_languages)
		if selection is None:
			return recurse_on_invalid_input(self._select_language)

		elif selection == 'English':
			eligible_languages.remove('English')
			reference_language_validity = False

			while not reference_language_validity:
				reference_language = resolve_input(input('Enter desired reference language: \n').title(), eligible_languages)
				if reference_language is None:
					print("Couldn't resolve input")
					time.sleep(1)
				else:
					selection = reference_language
					self.train_english, reference_language_validity = [True]*2
		return selection

	# -----------------
	# .MODE
	# -----------------
	class Mode(ExtendedEnum):
		VocabularyAcquisition = 'vocabulary acquisition'
		Lowkey = 'lowkey'
		Random = 'random'

	def _select_mode(self) -> str:
		explanations = (
			'show me sentences possessing an increased probability of containing rather infrequently used vocabulary',
			'show me sentences comprising exclusively commonly used vocabulary',
			'just hit me with dem sentences brah')

		clear_screen()

		print('TRAINING MODES\n')
		for i in range(3):
			print(f'{self.Mode.values()[i].title()}: ')
			print('\t', explanations[i])
		print('\nEnter desired mode:\t')
		mode_selection = resolve_input(input().lower(), self.Mode.values())
		if mode_selection is None:
			return recurse_on_invalid_input(self._select_mode)
		return mode_selection

	def _filter_sentences_mode_accordingly(self, mode: str):
		stems_2_indices = Stem2SentenceIndices.from_sentence_data(self._sentence_data, self.stemmer)

		def get_limit_corresponding_sentence_indices(occurrence_limit: int, filter_mode: str) -> List[int]:
			assert filter_mode in ['max', 'min']
			operator = ge if filter_mode == 'min' else le
			return list(chain.from_iterable((indices for indices in stems_2_indices.values() if operator(len(indices), occurrence_limit))))

		if mode == self.Mode.VocabularyAcquisition.value:
			indices = get_limit_corresponding_sentence_indices(20, 'max')
		else:
			indices = get_limit_corresponding_sentence_indices(50, 'min')
		print('Getting corresponding sentences...')
		self._sentence_data = self._sentence_data[indices]

	def _display_pre_training_instructions(self):
		clear_screen()

		print((f"Database comprises {len(self._sentence_data):,d} sentences.\n"
		"Hit\n "
		"\t- Enter to advance to next sentence\n"
		"Enter \n"
			"\t- 'vocabulary' to append new entry to language specific vocabulary file\n" 
			"\t- 'exit' to terminate program\n"
			"\t- 'alter' in order to alter the most recently added vocable entry\n"))

		lets_go_translation = self._find_lets_go_translation()
		print(lets_go_translation, '\n') if lets_go_translation is not None else print("Let's go!", '\n')

	# -----------------
	# TRAINING LOOP
	# -----------------
	def _train(self):
		class Option(ExtendedEnum):
			Exit = 'exit'
			AppendVocabulary = 'vocabulary'
			AlterLatestVocableEntry = 'alter'

		suspend_resolution = False
		def maintain_resolution_suspension():
			nonlocal suspend_resolution
			print(" ")
			suspend_resolution = True

		def maintain_resolution_suspension_and_erase_lines(n_lines: int):
			maintain_resolution_suspension()
			erase_lines(n_lines)

		np.random.shuffle(self._sentence_data)
		most_recent_vocable_entry: Optional[str] = None  # 'token - meaning'

		INDENTATION = '\t' * 2

		while True:
			if not suspend_resolution:
				try:
					reference_sentence, translation = self._sentence_data[self._n_trained_items]
				except (ValueError, IndexError):
					continue
				if any(default_name in reference_sentence for default_name in self.DEFAULT_NAMES) and self._names_convertible:
					reference_sentence, translation = map(self._accommodate_names_of_sentence, [reference_sentence, translation])

				self._buffer_print(INDENTATION, reference_sentence, '\t')
			else:
				suspend_resolution = False
			try:
				response = resolve_input(input("\t\tpending... ").lower(), Option.values())
				if response is not None:
					if response == Option.AppendVocabulary.value:
						most_recent_vocable_entry, n_printed_lines = self._insert_vocable_into_database()
						maintain_resolution_suspension_and_erase_lines(n_lines=n_printed_lines+1)

					elif response == Option.AlterLatestVocableEntry.value:
						if most_recent_vocable_entry is None:
							print("You haven't added any vocabulary during the current session")
							time.sleep(1)
							maintain_resolution_suspension_and_erase_lines(n_lines=2)
						else:
							altered_entry, n_printed_lines = self._modify_latest_vocable_insertion(most_recent_vocable_entry)
							if altered_entry is not None:
								most_recent_vocable_entry = altered_entry
							maintain_resolution_suspension_and_erase_lines(n_lines=n_printed_lines)

					elif response == Option.Exit.value:
						print('\n----------------')
						print("Number of faced sentences: ", self._n_trained_items)
						return
			except (KeyboardInterrupt, SyntaxError):
				pass

			erase_lines(1)
			if not suspend_resolution:
				self._buffer_print(INDENTATION, translation, '\n', INDENTATION, '_______________')
				self._n_trained_items += 1

				if self._n_trained_items >= 5:
					self._buffer_print.partially_redo_buffered_output(n_lines_to_be_removed=2)


	def _modify_latest_vocable_insertion(self, latest_appended_vocable_line: str) -> Tuple[Optional[str], int]:
		""" Returns:
		 		altered entry: str, None in case of invalid alteration
		 		n_printed_lines: int """

		old_token = latest_appended_vocable_line.split(' - ')[0]
		KeyboardController().type(f'{latest_appended_vocable_line}')
		new_entry = input('')
		new_split_entry = new_entry.split(' - ')
		if new_split_entry.__len__() == 1 or not all(new_split_entry):
			print('Invalid alteration')
			time.sleep(1)
			return None, 3
		self._database_client.alter_vocable_entry(old_token, *new_split_entry)
		return new_entry, 2


if __name__ == '__main__':
	SentenceTranslationTrainer(MongoDBClient('janek', None, MongoDBClient.Credentials.default()))