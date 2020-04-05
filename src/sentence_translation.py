import sys
import os
import platform
import time
from datetime import date
import json
from typing import List
from itertools import groupby
from bisect import insort

import numpy as np
import matplotlib.pyplot as plt

from .web_interaction import ContentRetriever


class SentenceTranslationTrainer:
	DEFAULT_NAMES = ['Tom', 'Mary']
	LANGUAGE_CORRESPONDING_NAMES = {'Italian': ['Alessandro', 'Christina'],
				  'French': ['Antoine', 'Amelie'],
				  'Spanish': ['Emilio', 'Luciana'],
				  'Hungarian': ['László', 'Zsóka'],
				  'German': ['Günther', 'Irmgard']}

	def __init__(self):
		self.base_data_path = os.path.join(os.getcwd(), 'language_data')
		self.date = str(date.today())

		self.reference_language_inversion = False

		self._language = None  # equals reference language in case of reference language inversion
		self.sentence_data = None

		self.webpage_interactor = ContentRetriever()

		self.chronic_file = os.path.join(os.getcwd(), 'exercising_chronic.json')

	@property
	def language(self):
		return self._language if not self.reference_language_inversion else 'English'

	@language.setter
	def language(self, value):
		self._language = value

	@property
	def sentence_file_path(self):
		return f'{self.base_data_path}/{self._language}/sentence_data.txt'

	@property
	def vocabulary_file_path(self):
		return f'{self.base_data_path}/{self.language}/vocabulary.txt'

	@staticmethod
	def clear_screen():
		os.system('cls' if platform.system() == 'Windows' else 'clear')

	@staticmethod
	def erase_previous_line():
		sys.stdout.write("\033[F")
		sys.stdout.write("\033[K")

	def run(self):
		# self.display_starting_screen()
		self.language = self.choose_language()
		if self._language not in os.listdir(self.base_data_path):
			zip_file_link = self.webpage_interactor.download_zipfile(self._language)
			self.webpage_interactor.unzip_file(zip_file_link)
		self.sentence_data = self.load_sentence_data()
		self.pre_exec_display()
		self.training_loop()

	def display_starting_screen(self):
		banner = open(os.path.join(os.getcwd(), 'ressources/banner.txt'), 'r').read()
		print(banner)
		print("							W2SV", '\n' * 1)
		print("					         by Janek Zangenberg ", '\n' * 2)

		time.sleep(3)
		self.clear_screen()

	# ---------------
	# INITIALIZATION
	# ---------------
	def choose_language(self) -> str:
		def indicate_invalid_selection():
			print('Invalid selection')
			time.sleep(1)

		webpage_request_success = self.webpage_interactor.get_language_ziplink_dict()
		eligible_languages = list(self.webpage_interactor.languages_2_ziplinks.keys()) if webpage_request_success else os.listdir(self.base_data_path)
		insort(eligible_languages, 'English')

		if len(eligible_languages) == 1:  # solely artificially appended english
			print('Please establish an internet connection in order to download sentence data.')
			print('Terminating program.')
			time.sleep(3)
			sys.exit(0)

		starting_letter_grouped = groupby(eligible_languages, lambda x: x[0])
		print('Eligible languages: '.upper())
		for _, values in starting_letter_grouped:
			print(', '.join(list(values)))

		selection = input('\nWhich language do you want to practice your yet demigodlike skills in? \n').title()
		if selection not in eligible_languages:
			indicate_invalid_selection()
			self.clear_screen()
			return self.choose_language()

		elif selection == 'English':
			reference_language_validity = False

			while not reference_language_validity:
				reference_language = input('Enter desired reference language: \n').title()
				if reference_language not in eligible_languages:
					indicate_invalid_selection()
				else:
					selection = reference_language
					self.reference_language_inversion, reference_language_validity = [True]*2

		return selection

	def load_sentence_data(self) -> np.ndarray:
		data = open(self.sentence_file_path, 'r', encoding='utf-8').readlines()
		split_data = [i.split('\t') for i in data]

		# remove reference appendices from source file if still present
		if len(split_data[0]) > 2:
			bilateral_sentences = ('\t'.join(row_splits[:2]) + '\n' for row_splits in split_data)
			with open(self.sentence_file_path, 'w', encoding='utf-8') as write_file:
				write_file.writelines(bilateral_sentences)

		for i, row in enumerate(split_data):
			split_data[i][1] = row[1].strip('\n')

		if self.reference_language_inversion:
			split_data = [list(reversed(row)) for row in split_data]

		return np.array(split_data)

	def pre_exec_display(self):
		self.clear_screen()
		instruction_text = f"""Data file comprises {len(self.sentence_data):,d} sentences.\nPress Enter to advance to next sentence, v to append new entry to language corresponding vocabulary text file.\nType 'exit' to terminate program.\n"""
		print(instruction_text)

		lets_go_occurrence_range = ((sentence_pair[0], i) for i, sentence_pair in enumerate(self.sentence_data[:int(len(self.sentence_data)*0.3)]))

		for content, i in lets_go_occurrence_range:
			if content == "Let's go!":
				print(self.sentence_data[i][1], '\n')
				return

		print("Let's go!", '\n')

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
	# EXECUTION
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

	def training_loop(self):
		faced_sentences = 0
		indices = np.arange(len(self.sentence_data))
		np.random.shuffle(indices)
		self.sentence_data = self.sentence_data[indices]

		while True:
			reference_sentence, translation = self.sentence_data[faced_sentences]
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
						print("Number of faced sentences: ", faced_sentences)
						doc_dict = self.add_number_2_file(faced_sentences)
						if faced_sentences > 4:
							self.visualize_exercising_chronic(doc_dict)
						sys.exit()
				except KeyboardInterrupt:
					print("Enter 'exit' to terminate program.")

			except SyntaxError:  # progressing with enter stroke
				pass
			self.erase_previous_line()
			print(translation, '\n', '_______________')
			faced_sentences += 1
	
	# ---------------
	# PROGRAM TERMINATION
	# ---------------
	def add_number_2_file(self, n_faced_sentences):
		if not os.path.isfile(self.chronic_file):
			# create new documentation dict
			with open(self.chronic_file, 'w+') as empty_file:
				doc_dict = {self.language: {self.date: n_faced_sentences}}
				json.dump(doc_dict, empty_file)
		else:
			with open(self.chronic_file) as read_file:
				doc_dict = json.load(read_file)
			
			if self.language in doc_dict.keys():
				date_dict = doc_dict[self.language]
				if self.date in date_dict.keys():
					date_dict[self.date] += n_faced_sentences
				else:
					date_dict[self.date] = n_faced_sentences
				doc_dict[self.language] = date_dict
			else:
				doc_dict[self.language] = {self.date: n_faced_sentences}
			
			with open(self.chronic_file, 'w+') as write_file:
				json.dump(doc_dict, write_file)

		return doc_dict

	def visualize_exercising_chronic(self, doc_dict):
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
