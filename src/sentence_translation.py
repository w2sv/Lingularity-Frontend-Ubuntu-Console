import sys
import os
import time
from datetime import date
import json
from typing import List
from itertools import groupby, chain
from bisect import insort

import numpy as np
import matplotlib.pyplot as plt

from .trainer import Trainer
from .web_interaction import ContentRetriever


# TODO: difficulty selection amelioration


class SentenceTranslationTrainer(Trainer):
	DEFAULT_NAMES = ['Tom', 'Mary']
	LANGUAGE_CORRESPONDING_NAMES = {'Italian': ['Alessandro', 'Christina'],
				  'French': ['Antoine', 'Amelie'],
				  'Spanish': ['Emilio', 'Luciana'],
				  'Hungarian': ['László', 'Zsóka'],
				  'German': ['Günther', 'Irmgard']}

	def __init__(self):
		super().__init__()
		self.date = str(date.today())

		self.webpage_interactor = ContentRetriever()

		self.chronic_file = os.path.join(os.getcwd(), 'exercising_chronic.json')

	def run(self):
		self.language = self.select_language()
		if self._language not in os.listdir(self.base_data_path):
			zip_file_link = self.webpage_interactor.download_zipfile(self._language)
			self.webpage_interactor.unzip_file(zip_file_link)
		self.sentence_data = self.parse_sentence_data()
		self.introduce_complexity()
		self.pre_training_display()
		self.train()

	# ---------------
	# INITIALIZATION
	# ---------------
	def select_language(self) -> str:
		print('Trying to connect to webpage...')
		webpage_request_success = self.webpage_interactor.get_language_ziplink_dict()
		eligible_languages = list(self.webpage_interactor.languages_2_ziplinks.keys()) if webpage_request_success else os.listdir(self.base_data_path)
		insort(eligible_languages, 'English')

		self.clear_screen()
		if len(eligible_languages) == 1:  # solely artificially appended english
			print('Please establish an internet connection in order to download sentence data.')
			print('Terminating program.')
			time.sleep(3)
			sys.exit(0)

		elif webpage_request_success == 0:
			print("Couldn't establish a connection")

		starting_letter_grouped = groupby(eligible_languages, lambda x: x[0])
		print('Eligible languages: '.upper())
		for _, values in starting_letter_grouped:
			print(', '.join(list(values)))

		selection = self.resolve_input(input('\nSelect language: \n').title(), eligible_languages)
		if selection is None:
			self.recurse_on_invalid_input(self.select_language)

		elif selection == 'English':
			eligible_languages.remove('English')
			reference_language_validity = False

			while not reference_language_validity:
				reference_language = self.resolve_input(input('Enter desired reference language: \n').title(), eligible_languages)
				if reference_language is None:
					print("Couldn't resolve input")
					time.sleep(1)
				else:
					selection = reference_language
					self.reference_language_inversion, reference_language_validity = [True]*2

		return selection

	def introduce_complexity(self):
		""" to be ML boosted or
		improved by introducing word occurrence based weight value function regarding entire sentence """

		difficulty_2_coefficient = {'easy': 0, 'medium': 1, 'hard': 2}

		self.clear_screen()
		print('Select difficulty:\t', '\t\t'.join([diff.title() for diff in difficulty_2_coefficient.keys()]))
		level_selection = self.resolve_input(input().lower(), list(difficulty_2_coefficient.keys()))
		if level_selection is None:
			self.recurse_on_invalid_input(self.introduce_complexity)

		elif level_selection == 'easy':
			return

		token_2_sentenceinds = self.procure_token_2_rowinds_map()

		occurence_distribution = [len(v) for v in token_2_sentenceinds.values()]
		min_occ, max_occ = min(occurence_distribution), max(occurence_distribution)
		step_size = (max_occ - min_occ) / len(difficulty_2_coefficient)

		min_occurrence = step_size * (difficulty_2_coefficient[level_selection] + 1) + min_occ
		indices = list(set(chain.from_iterable((v for v in token_2_sentenceinds.values() if len(v) >= min_occurrence))))
		self.sentence_data = self.sentence_data[indices]

	def pre_training_display(self):
		self.clear_screen()
		instruction_text = f"""Data file comprises {len(self.sentence_data):,d} sentences.\nPress Enter to advance to next sentence, v to append new entry to language corresponding vocabulary text file.\nEnter 'exit' to terminate program.\n"""
		print(instruction_text)

		lets_go_translation = self.get_lets_go_translation()
		print(lets_go_translation, '\n') if lets_go_translation is not None else print("Let's go!", '\n')

	# ----------------
	# VOCABULARY FILE
	# ----------------
	def append_2_vocabulary_file(self):
		word = input('Enter word in reference language: ')
		translation = input('Enter translation: ')

		with open(self.vocabulary_file_path, 'a+') as vocab_file:
			if os.path.getsize(self.vocabulary_file_path):
				vocab_file.write('\n') 
			vocab_file.write(f'{word} - {translation}')
		[self.erase_previous_line() for _ in range(2)]

	# -----------------
	# TRAINING LOOP
	# -----------------
	def convert_names(self, sentence_pair: List[str]) -> List[str]:
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

	def train(self):
		indices = np.arange(len(self.sentence_data))
		np.random.shuffle(indices)
		self.sentence_data = self.sentence_data[indices]

		while True:
			try:
				reference_sentence, translation = self.sentence_data[self.n_trained_items]
			except ValueError as ve:
				print(ve)
				continue
			if any(name in reference_sentence for name in self.DEFAULT_NAMES):
				reference_sentence, translation = self.convert_names([reference_sentence, translation])

			print(reference_sentence, '\t')
			try:
				try:
					response = input("pending...")
					if response == 'v':
						self.append_2_vocabulary_file()
						print(" ")

					elif response.lower() == 'exit':
						print("Number of faced sentences: ", self.n_trained_items)
						doc_dict = self.append_2_training_history(self.n_trained_items)
						if self.n_trained_items > 4:
							self.visualize_exercising_chronic(doc_dict)
						sys.exit()
				except KeyboardInterrupt:
					print("Enter 'exit' to terminate program.")

			except SyntaxError:  # progressing with enter stroke
				pass
			self.erase_previous_line()
			print(translation, '\n', '_______________')
			self.n_trained_items += 1
	
	# ---------------
	# PROGRAM TERMINATION
	# ---------------
	def visualize_exercising_chronic(self, doc_dict):
		plt.style.use('dark_background')

		date_dict = doc_dict[self.language]
		
		items = date_dict.items()
		# convert postunzipped tuples to lists for subsequent date assignment 
		dates, sentence_amounts = map(lambda x: list(x), zip(*items))
		
		# ommitting year, inverting day & month for proper tick label display
		for i, date in enumerate(dates):
			date_components = date.split('-')[1:]
			dates[i] = '-'.join(date_components[::-1])

		fig, ax = plt.subplots()
		fig.canvas.draw()
		fig.canvas.set_window_title("Way to go!")

		x_range = np.arange(len(items))
		ax.plot(x_range, sentence_amounts, marker='.', markevery=list(x_range), color='r')
		ax.set_xticks(x_range)
		ax.set_xticklabels(dates, minor=False, rotation=45)
		ax.set_title(f'{self.language} exercising chronic')
		ax.set_ylabel('number of sentences')
		ax.set_ylim(bottom=0)
		plt.show()		

	def last_session_display(self):
		pass


if __name__ == '__main__':
	SentenceTranslationTrainer().run()
