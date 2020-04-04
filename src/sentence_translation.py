import sys
import os
import time
from datetime import date
import json
from typing import List, ClassVar

import numpy as np
import matplotlib.pyplot as plt


class SentenceTranslationTrainer:
	default_names = ['Tom', 'Mary']
	names_dict = {'ita': ['Alessandro', 'Christina'], 'fre': ['Antoine', 'Amelie'], 'spa': ['Emilio', 'Luciana'], 'hun': ['László', 'Zsóka'], 'deu': ['Günther', 'Irmgard']}
	full_language_names = {'ita': 'Italian', 'fre': 'French', 'hun': 'Hungarian', 'por': 'Portuguese', 'spa': 'Spanish', 'deu': 'German'}

	def __init__(self):
		self.data_path = os.path.join(os.getcwd(), 'LanguageData')
		self.eligible_languages: List[str] = [i[:3] for i in os.listdir(self.data_path)]
		self.date = str(date.today())

		self.language_abb = None
		self.language_file_path = None
		self.sentence_data = None
		self.vocabulary_file_link = None

		self.chronic_file = os.path.join(os.getcwd(), 'exercising_chronic.json')

	@staticmethod
	def index(liste, targetvalue):
		for i in range(len(liste)):
			if liste[i] == targetvalue:
				return i
		return None

	@staticmethod
	def clear_screen():
		os.system('cls' if os.name == 'nt' else 'clear')

	def run(self):
		self.display_starting_screen()
		self.choose_language()
		self.sentence_data = self.load_sentence_data()
		self.vocabulary_file_link = self.get_vocabulary_file_link()
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
	def choose_language(self) -> ClassVar:
		print("Eligible languages: ", end="")
		[print(lan[:3].upper(), end=" " if ind < len(self.eligible_languages)-1 else '\n') for ind, lan in enumerate(self.eligible_languages)]

		language = input("Which language do you want to practice your yet demigodlike skills in? \n")
		language_abb = language[:3].lower()
		
		if language_abb not in self.eligible_languages:
			print('Invalid language')
			time.sleep(1)
			self.clear_screen()
			return self.choose_language()

		self.language_abb = language_abb
		self.language_file_path = f"{self.data_path}/{self.language_abb}.txt"

	def load_sentence_data(self) -> np.ndarray:
		data = open(self.language_file_path, 'r', encoding='utf-8').readlines()
		data = [i.split('\t') for i in data]
		return [[i[0], i[1].strip('\n')] for i in data]

	def pre_exec_display(self):
		self.clear_screen()
		print(f"Data file comprises {len(self.sentence_data):,d} sentences.")
		print("Press Enter to advance to next sentence, v to append new entry to language corresponding vocabulary text file.")
		print("Type 'exit' to terminate program.")

		lets_go_dict = {'spa': '¡Vamonos!', 'fre': 'Allons-y!', 'deu': "Auf geht's! ", 'ita': 'Andiamo!', 'hun': 'Kezdjük el!', 'por': 'Vamos!'}
		print(lets_go_dict.get(self.language_abb), '\n')

	# ----------------
	# VOCABULARY FILE
	# ----------------
	def get_vocabulary_file_link(self) -> str:
		vocab_dir = os.path.join(os.path.join(os.getcwd(), 'Vocabulary'))
		if not os.path.isdir(vocab_dir):
			os.mkdir(vocab_dir)

		return os.path.join(vocab_dir, f'{self.full_language_names[self.language_abb]}.txt')

	def append_2_vocabulary_file(self):
		word = input('Enter word: ')
		translation = input('Enter translation: ')

		with open(self.vocabulary_file_link, 'a+') as vocab_file:
			if os.path.getsize(self.vocabulary_file_link):
				vocab_file.write('\n') 
			vocab_file.write(f'{word} - {translation}')
			print('Appended to vocabulary file')

	# -----------------
	# EXECUTION
	# -----------------
	def convert_names(self, sentence_pair: List[str]):		
		"""
		 	stores sentence finishing punctuation instance to enable 
		    the finding of default names directly attached to
		 	aforementioned and reinserts it afterwards
		""" 

		if self.names_dict.get(self.language_abb) is not None:
			punctuation = sentence_pair[0][-1]
			
			for sentence_ind, sentence in enumerate(sentence_pair):
				sentence_tokens = sentence[:-1].split(' ')
				
				for name_ind, name in enumerate(self.default_names):
					ind = self.index(sentence_tokens, name)
					if ind is not None:
						sentence_tokens[ind] = self.names_dict[self.language_abb][name_ind]
				sentence_pair[sentence_ind] = ' '.join(sentence_tokens) + punctuation

			return sentence_pair

	def training_loop(self):
		faced_sentences = 0
		indices = np.arange(len(self.sentence_data))
		np.random.shuffle(indices)
		self.sentence_data = self.sentence_data[indices]

		while True:
			sentence_pair = self.sentence_data[faced_sentences]
			if any(name in sentence_pair[0] for name in self.default_names):
				sentence_pair = self.convert_names(sentence_pair)

			print(sentence_pair[0], '\t')
			try:
				try:
					response = input("pending...")
					if response == 'v':
						self.append_2_vocabulary_file()
						print(" ")

					elif response.lower() == 'exit':
						print("Number of faced sentences: ",faced_sentences)
						doc_dict = self.add_number_2_file(faced_sentences)
						if faced_sentences > 4:
							self.visualize_exercising_chronic(doc_dict)
						sys.exit()
				except KeyboardInterrupt:
					print("Enter 'exit' to terminate program.")

			except SyntaxError:  # progressing with enter stroke
				pass
			print(sentence_pair[1], '\n', '_______________')
			faced_sentences += 1
	
	# ---------------
	# PROGRAM TERMINATION
	# ---------------
	def add_number_2_file(self, n_faced_sentences):
		if not os.path.isfile(self.chronic_file):
			# create new documentation dict
			with open(self.chronic_file, 'w+') as empty_file:
				doc_dict = {self.language_abb: {self.date: n_faced_sentences}}
				json.dump(doc_dict, empty_file)
		else:
			with open(self.chronic_file) as read_file:
				doc_dict = json.load(read_file)
			
			if self.language_abb in doc_dict.keys():
				date_dict = doc_dict[self.language_abb]
				if self.date in date_dict.keys():
					date_dict[self.date] += n_faced_sentences
				else:
					date_dict[self.date] = n_faced_sentences
				doc_dict[self.language_abb] = date_dict
			else:
				doc_dict[self.language_abb] = {self.date: n_faced_sentences}
			
			with open(self.chronic_file, 'w+') as write_file:
				json.dump(doc_dict, write_file)

		return doc_dict

	def visualize_exercising_chronic(self, doc_dict):
		date_dict = doc_dict[self.language_abb]
		
		items = date_dict.items()
		# convert postunzipped tuples to lists for subsequent date assignment 
		dates, sentence_amounts = map(lambda x: list(x), zip(*items))
		
		# ommitting year, inverting day & month for proper tick label display
		for i, date in enumerate(dates):
			date_components = date.split('-')[1:]
			dates[i] = '-'.join(date_components[::-1])

		fig, ax = plt.subplots()
		fig.canvas.draw()
		fig.canvas.set_window_title("You had in the very least one more in the tank...")

		x_range = np.arange(len(items))
		ax.plot(x_range, sentence_amounts, marker='.', markevery=list(x_range), color='r')
		ax.set_xticks(x_range)
		ax.set_xticklabels(dates, minor=False, rotation=45)
		ax.set_title(f'{self.full_language_names[self.language_abb]} exercising chronic')
		ax.set_ylabel('number of sentences')
		ax.set_ylim(bottom=0)
		plt.show()		

	def last_session_display(self):
		pass


if __name__ == '__main__':
	SentenceTranslationTrainer().run()
