from typing import List, Dict, Optional, Tuple, Any
import os
import sys
import json
from collections import Counter
import datetime
from itertools import chain
from time import time, sleep
import time
import signal

import unidecode
import numpy as np
import matplotlib.pyplot as plt

from .trainer import Trainer, TokenSentenceindsMap
from .sentence_translation import SentenceTranslationTrainer


TrainingDocumentation = Dict[str, Dict[str, Any]]  # entry -> Dict[score: float, times_seen: int, last_seen_date: str]


# TODO: training documentation, append new meanings, progress plotting, vocabulary statistics, prioritizazion
#  motivation throughout training, english training
#  sentence finding for other translation tokens


class VocabularyTrainer(Trainer):
    RESPONSE_EVALUATIONS = {0: 'wrong', 1: 'accent fault', 2: 'correct', 3: 'perfect'}
    COMPLETION_SCORE = 5
    N_RELATED_SENTENCES = 2
    ROOT_LENGTH = 4
    N_RETENTION_ASSERTION_DAYS = 50
    PERCENTAGE_VERDICTS = {
               0: 'You suck.',
               20: 'Get your shit together m8.',
               40: "You can't climb the ladder of success with your hands in your pockets.",
               60: "Keep hustlin' young blood.",
               80: 'Attayboy!',
               100: '0361/2180494. Call me.'}

    def __init__(self):
        super().__init__()

        self.token_2_rowinds: Optional[TokenSentenceindsMap] = None
        self.vocabulary_statistics: Optional[TrainingDocumentation] = None
        self.vocabulary: Optional[Dict[str, str]] = None

        self.reference_2_foreign = True
        self.reverse_response_evaluations = {v: k for k, v in self.RESPONSE_EVALUATIONS.items()}

        self.n_trained, self.n_correct_responses = [0] * 2

    @property
    def voccabulary_statistics_file_path(self):
        return f'{self.base_data_path}/{self.language}/vocabulary_statistics.json'

    def run(self):
        self._language = self.select_language()
        self.sentence_data = self.parse_sentence_data()
        self.token_2_rowinds = self.procure_token_2_rowinds_map()
        self.vocabulary = self.parse_vocabulary()
        self.vocabulary_statistics = self.load_vocabulary_statistics()
        self.update_documentation()
        self.display_new_vocabulary()
        self.pre_training_display()
        self.train()
        self.save_vocabulary_documentation()
        self.append_2_training_documentation()
        # self.pie_chart_display()
        # self.exit_screen()

    # ---------------
    # INITIALIZATION
    # ---------------
    def select_language(self) -> str:
        eligible_languages = [language for language in os.listdir(self.base_data_path) if 'vocabulary.txt' in os.listdir(f'{self.base_data_path}/{language}')]
        if not eligible_languages:
            print('You have to accumulate vocabulary by means of the SentenceTranslation™ Trainer or manual amassment first.')
            sleep(3)
            print('Starting SentenceTranslation Trainer...')
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
            return {target_language_entry: translation.strip('\n') for target_language_entry, translation in [row.split(' - ') for row in  file.readlines()]}

    def load_vocabulary_statistics(self) -> Optional[TrainingDocumentation]:
        """ structure: entry -> Dict[score, n_seen, date last seen] """
        if not os.path.exists(self.voccabulary_statistics_file_path):
            return None

        with open(self.voccabulary_statistics_file_path) as read_file:
            return json.load(read_file)

    def update_documentation(self):
        # TODO: account for target language entry changes

        INIT = {'s': 0, 'tf': 0, 'lfd': None}

        # create new documentation file if necessary
        if self.vocabulary_statistics is None:
            self.vocabulary_statistics = {entry: INIT.copy() for entry in self.vocabulary.keys()}

        for entry in self.vocabulary.keys():
            if self.vocabulary_statistics.get(entry) is None:
                self.vocabulary_statistics[entry] = INIT

    def display_new_vocabulary(self):
        self.clear_screen()
        display_vocabulary = self.resolve_input(input('Do you want new vocabulary to be displayed once? (y)es/(n)o\n').lower(), ['yes', 'no'])
        if display_vocabulary == 'yes':
            new_vocabulary = [key for key in self.vocabulary_statistics.keys() if self.vocabulary_statistics[key]['lfd'] is None]
            if not new_vocabulary:
                return
            [print('\t', entry, ' = ', self.vocabulary[entry]) for entry in new_vocabulary]
            print('\n')
            input('Press any key to continue')

    def pre_training_display(self):
        self.clear_screen()
        n_imperfect_entries = len([e for e in self.vocabulary_statistics.values() if e['s'] < self.COMPLETION_SCORE])
        print(f'Vocabulary file comprises {n_imperfect_entries} entries.')

        lets_go_translation = self.get_lets_go_translation()
        print(lets_go_translation, '\n') if lets_go_translation is not None else print("Let's go!", '\n')

    # ------------------
    # TRAINING
    # ------------------
    @staticmethod
    def day_difference(date: str) -> int:
        return (datetime.date.today() - datetime.datetime.strptime(date, '%Y-%M-%d')).days

    def train(self):
        entries = [entry for entry in self.vocabulary.keys() if self.vocabulary_statistics[entry]['s'] < 5 or self.day_difference(self.vocabulary_statistics[entry]['lfd']) >= self.N_RETENTION_ASSERTION_DAYS]
        np.random.shuffle(entries)

        get_display_token = lambda entry: self.vocabulary[entry] if self.reference_2_foreign else entry
        get_translation = lambda entry: entry if self.reference_2_foreign else self.vocabulary[entry]

        for entry in entries:
            display_token, translation = get_display_token(entry), get_translation(entry)
            response = input(f'{display_token} = ')
            if response.lower() == 'exit':
                break

            response_evaluation = self.evaluate_response(response, translation)

            print('\t', self.RESPONSE_EVALUATIONS[response_evaluation].upper(), end=' ')
            if self.RESPONSE_EVALUATIONS[response_evaluation] != 'perfect':
                print('| Correct translation: ', translation, end='')
            print('')
            comprising_sentences = self.get_comprising_sentences(entry.split(',')[0])
            if comprising_sentences is not None:
                [print('\t', s) for s in comprising_sentences]
            print('_______________')

            self.update_documentation_entry(entry, response_evaluation)

            self.n_trained += 1
            if self.RESPONSE_EVALUATIONS[response_evaluation] != 'wrong':
                self.n_correct_responses += 1

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

    def __get_root_comprising_tokens(self, root) -> List[str]:
        return [k for k in self.token_2_rowinds.keys() if root in k]

    def get_root_comprising_sentence_inds(self, root: str) -> List[int]:
        return list(chain.from_iterable([v for k, v in self.token_2_rowinds.items() if root in k]))

    def get_root_preceded_token_comprising_sentence_inds(self, root: str) -> List[int]:
        """ not used """
        return list(chain.from_iterable([v for k, v in self.token_2_rowinds.items() if any(token.startswith(root) for token in k.split(' '))]))

    def get_comprising_sentences(self, token: str) -> Optional[List[str]]:
        root = token[:self.ROOT_LENGTH]
        sentence_indices = np.array(self.get_root_comprising_sentence_inds(root))
        if not len(sentence_indices):
            return None

        random_indices = np.random.randint(0, len(sentence_indices), self.N_RELATED_SENTENCES)
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
        return self.n_correct_responses / self.n_trained * 100

    @property
    def performance_verdict(self) -> str:
        return self.PERCENTAGE_VERDICTS[int(self.correctness_percentage) // 20 * 20]

    def exit_screen(self):
        print(f'You got {self.n_correct_responses}/{self.n_trained} correct, i.e. {int(self.correctness_percentage)}% right', '\n')
        time.sleep(3)
        print(self.performance_verdict)

    def pie_chart_display(self):
        correct_percentage = (self.n_correct_responses / self.n_trained) * 100
        incorrect_percentage = 100 - correct_percentage

        labels = ['Correct', 'Incorrect']
        explode = (0.1, 0)
        sizes = correct_percentage, incorrect_percentage
        colors = ['g', 'r']
        try:
            def retain_valid_value(*iterables):
                hundred_percent_index = [correct_percentage, incorrect_percentage].index(100)
                return ([i[hundred_percent_index]] for i in iterables)

            labels, explode, sizes, colors = retain_valid_value(labels, explode, sizes, colors)
        except ValueError:
            pass

        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, shadow=True, startangle=120, autopct='%1.1f%%', explode=explode, colors=colors)
        ax.axis('equal')
        ax.set_title(self.performance_verdict)
        fig.canvas.set_window_title(f'You got {self.n_correct_responses}/{self.n_trained} right')
        plt.show()

    def append_2_training_documentation(self):
        documentation = self.load_documentation()
        today = str(datetime.date.today())
        if today in documentation.keys():
            documentation[today]['v'] += self.n_trained
        else:
            documentation[today] = {'v': self.n_trained}
        with open(self.training_documentation_file_path, 'w+') as write_file:
            json.dump(documentation, write_file)

    def save_vocabulary_documentation(self):
        with open(self.voccabulary_statistics_file_path, 'w+') as dump_file:
            json.dump(self.vocabulary_statistics, dump_file)


if __name__ == '__main__':
    VocabularyTrainer().run()

