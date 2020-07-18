import sys
import os
import time
from typing import List
from itertools import groupby, chain
from bisect import insort
from operator import ge, le

import numpy as np
from pynput.keyboard import Controller as KeyboardController

from lingularity.trainers import Trainer
from lingularity.webpage_interaction import ContentRetriever
from lingularity.types.token_maps import Stem2SentenceIndices
from lingularity.utils.enum import ExtendedEnum
from lingularity.utils.output_manipulation import clear_screen, erase_previous_line
from lingularity.utils.input_resolution import resolve_input, recurse_on_invalid_input


class SentenceTranslationTrainer(Trainer):
	DEFAULT_NAMES = ('Tom', 'Mary')
	LANGUAGE_CORRESPONDING_NAMES = {
		'Italian': ['Alessandro', 'Christina'],
		'French': ['Antoine', 'Amelie'],
		'Spanish': ['Emilio', 'Luciana'],
		'Hungarian': ['László', 'Zsóka'],
		'German': ['Günther', 'Irmgard']
	}

	def __init__(self):
		self._content_retriever = ContentRetriever()

		super().__init__()


	def run(self):
		if self._language not in self.locally_available_languages:
			self._download_and_process_zip_file()

		self._sentence_data = self._parse_sentence_data()

		if (mode_selection := self._select_mode()) != self.Mode.Random.value:
			self._filter_sentences_mode_accordingly(mode_selection)

		self._display_pre_training_instructions()
		self._train()

	def _download_and_process_zip_file(self):
		zip_file_link = self._content_retriever.download_zipfile(self._language)
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
			"\t- 'modify' in order to modify latest vocabulary file entry\n"))

		lets_go_translation = self._find_lets_go_translation()
		print(lets_go_translation, '\n') if lets_go_translation is not None else print("Let's go!", '\n')

	# -----------------
	# TRAINING LOOP
	# -----------------
	def _train(self):
		class Option(ExtendedEnum):
			Exit = 'exit'
			AppendVocabulary = 'vocabulary'
			ModifyVocabulary = 'modify'

		suspend_resolution = False
		def maintain_resolution_suspension():
			nonlocal suspend_resolution
			print(" ")
			suspend_resolution = True

		np.random.shuffle(self._sentence_data)

		while True:
			if not suspend_resolution:
				try:
					reference_sentence, translation = self._sentence_data[self._n_trained_items]
				except (ValueError, IndexError):
					continue
				if any(name in reference_sentence for name in self.DEFAULT_NAMES):
					reference_sentence, translation = self._convert_names([reference_sentence, translation])

				print(reference_sentence, '\t')
			else:
				suspend_resolution = False
			try:
				response = resolve_input(input("pending...").lower(), Option.values())
				if response is not None:
					if response == Option.AppendVocabulary.value:
						self._append_2_vocabulary_file()
						maintain_resolution_suspension()
						erase_previous_line()

					elif response == Option.ModifyVocabulary.value:
						self._modify_last_vocabulary_file_entry()
						maintain_resolution_suspension()
						[erase_previous_line() for _ in range(3)]

					elif response == Option.Exit.value:
						print('----------------')
						print("Number of faced sentences: ", self._n_trained_items)
						self._append_2_training_history()
						if self._n_trained_items > 5:
							self._plot_training_history()
						sys.exit()
			except (KeyboardInterrupt, SyntaxError):
				pass

			erase_previous_line()
			if not suspend_resolution:
				print(translation, '\n', '_______________')
				self._n_trained_items += 1

	def _append_2_vocabulary_file(self):
		vocable = input(f'Enter {self.language} word/phrase: ')
		meanings = input('Enter meaning(s): ')

		with open(self.vocabulary_file_path, 'a+') as vocab_file:
			if os.path.getsize(self.vocabulary_file_path):
				vocab_file.write('\n')
			vocab_file.write(f'{vocable} - {meanings}')
		[erase_previous_line() for _ in range(2)]

	def _modify_last_vocabulary_file_entry(self):
		if not os.path.exists(self.vocabulary_file_path):
			print('There is no vocabulary to be modified yet')
			return
		print('Last _vocabulary file entry:\n\t', end='')
		with open(self.vocabulary_file_path, 'r+') as vocab_file:
			line_data = vocab_file.readlines()
			vocab_file.seek(0)
			KeyboardController().type(f'{line_data[-1]}')
			line_data[-1] = input('')
			vocab_file.writelines(line_data)
			vocab_file.truncate()

	def _convert_names(self, sentence_pair: List[str]) -> List[str]:
		if not self.LANGUAGE_CORRESPONDING_NAMES.get(self.language):
			return sentence_pair

		punctuation = sentence_pair[0][-1]
		for sentence_ind, sentence in enumerate(sentence_pair):
			sentence_tokens = sentence[:-1].split(' ')

			for name_ind, name in enumerate(self.DEFAULT_NAMES):
				try:
					ind = sentence_tokens.index(name)
					sentence_tokens[ind] = self.LANGUAGE_CORRESPONDING_NAMES[self.language][name_ind]
				except ValueError:
					pass
			sentence_pair[sentence_ind] = ' '.join(sentence_tokens) + punctuation

		return sentence_pair


if __name__ == '__main__':
	SentenceTranslationTrainer().run()
