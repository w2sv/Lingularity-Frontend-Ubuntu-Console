from typing import List, Dict, Optional, Union
import os
import sys
import json
from collections import Counter
import datetime
from time import time, sleep
import time

import unidecode
import numpy as np
import matplotlib.pyplot as plt

from src.trainers.trainer import Trainer
from src.trainers.sentence_translation import SentenceTranslationTrainer
from src.types.token_maps import RawToken2SentenceIndices
from src.utils.datetime import n_days_ago
from src.utils.strings import get_article_stripped_token


# TODO: english training, refactor vocabulary statistics, possibly vocabulary file to separate class


class VocabularyTrainer(Trainer):
    # foreign language token -> Dict[score: float, times_seen: int, last_seen_date: str]
    VocabularyStatistics = Dict[str, Dict[str, Union[float, int, str]]]

    RESPONSE_EVALUATIONS = {0: 'wrong', 1: 'accent fault', 2: 'correct', 3: 'perfect'}
    COMPLETION_SCORE = 5
    N_SENTENCES_TO_BE_DISPLAYED = 2
    ROOT_LENGTH = 4
    DAYS_TIL_RETENTION_ASSERTION = 50
    PERCENTAGE_CORRESPONDING_VERDICTS = {
        0: 'You suck.',
        20: 'Get your shit together m8.',
        40: "You can't climb the ladder of success with your hands in your pockets.",
        60: "Keep hustlin' young blood.",
        80: 'Attayboy!',
        100: '0361/2680494. Call me.'}

    def __init__(self):
        super().__init__()

        self.token_2_rowinds: Optional[RawToken2SentenceIndices] = None
        self.vocabulary_statistics: Optional[VocabularyTrainer.VocabularyStatistics] = None
        self.vocabulary: Optional[Dict[str, str]] = None

        self.reference_2_foreign = True
        self.reverse_response_evaluations: Dict[str, int] = {v: k for k, v in self.RESPONSE_EVALUATIONS.items()}

        self.n_correct_responses = 0
        self.display_new_vocabulary_absence = False

    @property
    def voccabulary_statistics_file_path(self):
        return f'{self.BASE_DATA_PATH}/{self.language}/vocabulary_statistics.json'

    def run(self):
        self._language = self.select_language()
        self.sentence_data = self.parse_sentence_data()
        self.token_2_rowinds = RawToken2SentenceIndices(self.sentence_data)
        self.vocabulary = self.parse_vocabulary()
        self.vocabulary_statistics = self.load_vocabulary_statistics()
        self.update_documentation()
        self.display_new_vocabulary()
        self.pre_training_display()
        self.train()
        self.save_vocabulary_statistics()
        self.append_2_training_history()
        self.display_pie_chart()
        self.plot_training_history()

    # ---------------
    # INITIALIZATION
    # ---------------
    def select_language(self) -> str:
        eligible_languages = [language for language in os.listdir(self.BASE_DATA_PATH) if 'vocabulary.txt' in os.listdir(f'{self.BASE_DATA_PATH}/{language}')]
        if not eligible_languages:
            print('You have to accumulate vocabulary by means of the SentenceTranslation™ Trainer or manual amassment first.')
            sleep(3)
            print('Initiating SentenceTranslation Trainer...')
            sleep(2)
            self.clear_screen()
            SentenceTranslationTrainer().run()
            sys.exit(0)

        print('ELIGIBLE LANGUAGES: ')
        [print(language) for language in sorted(eligible_languages)]
        language_selection = input('\nEnter desired language:\n').title()
        input_resolution = self.resolve_input(language_selection, eligible_languages)
        if input_resolution is None:
            return self.recurse_on_invalid_input(self.select_language)
        return input_resolution

    def parse_vocabulary(self) -> Dict[str, str]:
        with open(self.vocabulary_file_path, 'r') as file:
            return {target_language_entry: translation.strip('\n') for target_language_entry, translation in [row.split(' - ') for row in file.readlines()]}

    def load_vocabulary_statistics(self) -> Optional[VocabularyStatistics]:
        if not os.path.exists(self.voccabulary_statistics_file_path):
            return None

        with open(self.voccabulary_statistics_file_path) as read_file:
            return json.load(read_file)

    def update_documentation(self):
        # TODO: account for target language entry changes

        INIT = {'s': 0, 'tf': 0, 'lfd': None}  # score, times_faced, last_faced_date

        # create new documentation file if necessary
        if self.vocabulary_statistics is None:
            self.vocabulary_statistics = {entry: INIT.copy() for entry in self.vocabulary.keys()}

        for entry in self.vocabulary.keys():
            if self.vocabulary_statistics.get(entry) is None:
                self.vocabulary_statistics[entry] = INIT.copy()

    def display_new_vocabulary(self):
        self.clear_screen()
        display_vocabulary = self.resolve_input(input('Do you want new vocabulary to be displayed once before training? (y)es/(n)o\n').lower(), ['yes', 'no'])
        if display_vocabulary == 'yes':
            new_vocabulary = [key for key in self.vocabulary_statistics.keys() if self.vocabulary_statistics[key]['lfd'] is None]
            if not new_vocabulary:
                self.display_new_vocabulary_absence = True
                return
            [print('\t', entry, ' = ', self.vocabulary[entry]) for entry in new_vocabulary]
            print('\n')
            input('Press any key to continue')

    def pre_training_display(self):
        self.clear_screen()
        n_imperfect_entries = len([e for e in self.vocabulary_statistics.values() if e['s'] < self.COMPLETION_SCORE])
        if self.display_new_vocabulary_absence:
            print("Couldn't find any new vocabulary.\n")
        print(f'Vocabulary file comprises {n_imperfect_entries} entries.')
        print("Enter 'append' + additional translation(s) in order to append to the ones of the previously faced item.")
        print("Distinct newly entered translation tokens are to be separated by commas.")
        print("Enter 'exit' to terminate the program.", '\n')

        lets_go_translation = self.get_lets_go_translation()
        print(lets_go_translation, '\n') if lets_go_translation is not None else print("Let's go!", '\n')

    # ------------------
    # TRAINING
    # ------------------
    def append_translation(self, entry: str, additional_translations: str):
        additional_translations = additional_translations.rstrip().lstrip()

        # insert whitespaces after commas if not already present
        tokens = list(additional_translations)
        for i in range(len(tokens)-1, 1, -1):
            if tokens[i-1] == ',' and tokens[i] != ' ':
                tokens.insert(i, ' ')
        additional_translations = ''.join(tokens)

        with open(self.vocabulary_file_path, 'r') as read_file:
            vocabulary = read_file.readlines()
            split_data = [row.split(' - ') for row in vocabulary]
            corresponding_row_ind = [i for i in range(len(split_data)) if entry in split_data[i][0]][0]
            vocabulary[corresponding_row_ind] = vocabulary[corresponding_row_ind][:-1] + ', ' + additional_translations + '\n'

        with open(self.vocabulary_file_path, 'w') as write_file:
            write_file.writelines(vocabulary)

    def train(self):
        entries = [entry for entry in self.vocabulary.keys() if self.vocabulary_statistics[entry]['s'] < 5 or n_days_ago(self.vocabulary_statistics[entry]['lfd']) >= self.DAYS_TIL_RETENTION_ASSERTION]
        np.random.shuffle(entries)

        get_display_token = lambda entry: self.vocabulary[entry] if self.reference_2_foreign else entry
        get_translation = lambda entry: entry if self.reference_2_foreign else self.vocabulary[entry]

        i, display_item = 0, True
        while i < len(entries):
            entry = entries[i]
            display_token, translation = get_display_token(entry), get_translation(entry)
            print(f'{display_token} = ', end='') if display_item else print('Enter translation: ', end='')
            try:
                response = input()
            except KeyboardInterrupt:
                display_item = False
                continue
            if response.lower() == 'exit':
                break
            elif response.lower().startswith('append') and i:
                self.append_translation(entries[i-1], response[len('append'):])
                display_item = False
                continue

            response_evaluation = self.evaluate_response(response, translation)

            print('\t', self.RESPONSE_EVALUATIONS[response_evaluation].upper(), end=' ')
            if self.RESPONSE_EVALUATIONS[response_evaluation] != 'perfect':
                print('| Correct translation: ', translation, end='')
            print('')
            comprising_sentences = self.get_comprising_sentences(display_token)
            if comprising_sentences is not None:
                [print('\t', s) for s in comprising_sentences]
            print('_______________')

            self.update_documentation_entry(entry, response_evaluation)

            self.n_trained_items += 1
            if self.RESPONSE_EVALUATIONS[response_evaluation] != 'wrong':
                self.n_correct_responses += 1

            if i and not i % 9:
                print(f'{i} Entries faced, {len(entries) - i} more to go', '\n')

            i += 1
            display_item = True

    def evaluate_response(self, response: str, translation: str) -> int:
        distinct_translations = translation.split(',')
        accent_pruned_translations = list(map(unidecode.unidecode, distinct_translations))

        def tolerable_error():
            def n_deviations(a: str, b: str) -> int:
                def dict_value_sum(dictionary):
                    return sum(list(dictionary.values()))
                short, long = sorted([a, b], key=lambda string: len(string))
                short_c, long_c = map(Counter, [short, long])
                return dict_value_sum(long_c - short_c)

            TOLERATED_CHAR_DEVIATIONS = 1
            return any(n_deviations(response, translation) <= TOLERATED_CHAR_DEVIATIONS for translation in distinct_translations)

        distinct_translations = translation.split(',')
        if response in distinct_translations:
            evaluation = 'perfect'
        elif response in accent_pruned_translations:
            evaluation = 'accent fault'
        elif tolerable_error():
            evaluation = 'correct'
        else:
            evaluation = 'wrong'
        return self.reverse_response_evaluations[evaluation]

    def get_comprising_sentences(self, token: str) -> Optional[List[str]]:
        root = get_article_stripped_token(token)[:self.ROOT_LENGTH]
        sentence_indices = np.asarray(self.token_2_rowinds.get_root_comprising_sentence_indices(root))
        if not len(sentence_indices):
            return None

        random_indices = np.random.randint(0, len(sentence_indices), self.N_SENTENCES_TO_BE_DISPLAYED)
        return self.sentence_data[sentence_indices[random_indices]][:, 1]

    def update_documentation_entry(self, entry, response_evaluation):
        self.vocabulary_statistics[entry]['lfd'] = str(datetime.date.today())
        self.vocabulary_statistics[entry]['tf'] += 1
        if self.vocabulary_statistics[entry]['s'] == 5 and self.RESPONSE_EVALUATIONS[response_evaluation] != 'perfect':
            self.vocabulary_statistics[entry]['s'] -= 1
        else:
            self.vocabulary_statistics[entry]['s'] += 0.5 if self.RESPONSE_EVALUATIONS[response_evaluation] in ['accent fault', 'correct'] else response_evaluation // 3

    # -----------------
    # PROGRAM TERMINATION
    # -----------------
    @property
    def correctness_percentage(self) -> float:
        return self.n_correct_responses / self.n_trained_items * 100

    @property
    def performance_verdict(self) -> str:
        return self.PERCENTAGE_CORRESPONDING_VERDICTS[int(self.correctness_percentage) // 20 * 20]

    def display_pie_chart(self):
        correct_percentage = (self.n_correct_responses / self.n_trained_items) * 100
        incorrect_percentage = 100 - correct_percentage

        labels = ['Correct', 'Incorrect']
        explode = (0.1, 0)
        sizes = correct_percentage, incorrect_percentage
        colors = ['g', 'r']
        try:
            def discard_futile_value(*iterables):
                hundred_percent_index = [correct_percentage, incorrect_percentage].index(100)
                return ([i[hundred_percent_index]] for i in iterables)

            labels, explode, sizes, colors = discard_futile_value(labels, explode, sizes, colors)
        except ValueError:
            pass

        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, shadow=True, startangle=120, autopct='%1.1f%%', explode=explode, colors=colors)
        ax.axis('equal')
        ax.set_title(self.performance_verdict)
        fig.canvas.set_window_title(f'You got {self.n_correct_responses}/{self.n_trained_items} right')
        plt.show()

    def save_vocabulary_statistics(self):
        with open(self.voccabulary_statistics_file_path, 'w+') as dump_file:
            json.dump(self.vocabulary_statistics, dump_file)


if __name__ == '__main__':
    VocabularyTrainer().run()
