from typing import List, Dict, Optional, Tuple
import os
import json
from collections import Counter
from datetime import date
from itertools import chain
from time import time
import time

import unidecode
import numpy as np

from .trainer import Trainer, TokenSentenceindsMap


TrainingDocumentation = Dict[str, Dict[str, int, int]]  # entry -> Dict[score, times seen, last seen]


# TODO: training documentation, disabling strg + c, append new meanings, progress plotting, vocabulary statistics, prioritizazion
#  ignoring perfected vocabulary, motivation throughout training, english training, method structuring, display of new vocabulary if desired
#  sentence finding for other translation tokens


class VocabularyTrainer(Trainer):
    RESPONSE_EVALUATIONS = {0: 'wrong', 1: 'accent fault', 2: 'correct', 3: 'perfect'}
    COMPLETION_SCORE = 5
    N_RELATED_SENTENCES = 2
    ROOT_LENGTH = 4

    def __init__(self):
        super().__init__()

        self.token_2_rowinds: Optional[TokenSentenceindsMap] = None
        self.training_documentation: Optional[TrainingDocumentation] = None
        self.vocabulary: Optional[Dict[str, str]] = None

        self.reference_2_foreign = True
        self.reverse_response_evaluations = {v: k for k, v in self.RESPONSE_EVALUATIONS.items()}

        self.n_trained, self.n_correct_responses = [0] * 2

    @property
    def training_documentation_path(self):
        return f'{self.base_data_path}/{self.language}/vocabulary_training_documentation.json'

    def select_language(self) -> str:
        eligible_languages = [language for language in os.listdir(self.base_data_path) if 'vocabulary.txt' in os.listdir(f'{self.base_data_path}/{language}')]
        print('ELIGIBLE LANGUAGES: ')
        [print(language) for language in sorted(eligible_languages)]
        language_selection = input('\nEnter desired language:\n').title()
        input_resolution = self.resolve_input(language_selection, eligible_languages)
        if input_resolution is None:
            return self.recurse_on_invalid_input(self.select_language)
        return input_resolution

    def query_settings(self):
        pass

    def parse_vocabulary(self) -> Dict[str, str]:
        with open(self.vocabulary_file_path, 'r') as file:
            return {target_language_entry: translation.strip('\n') for target_language_entry, translation in [row.split(' - ') for row in  file.readlines()]}

    def load_training_documentation(self) -> Optional[TrainingDocumentation]:
        """ structure: entry -> Dict[score, n_seen, date last seen] """
        if not os.path.exists(self.training_documentation_path):
            return None

        with open(self.training_documentation_path) as read_file:
            return json.load(read_file)

    def update_documentation(self) -> TrainingDocumentation:
        # TODO: account for target language entry changes

        INIT = {'s': 0, 'tf': 0, 'lfd': None}

        # create new documentation file if necessary
        if not self.training_documentation:
            return {entry: INIT.copy() for entry in self.vocabulary.keys()}

        for entry in self.vocabulary.keys():
            if self.training_documentation.get(entry) is None:
                self.training_documentation[entry] = INIT
        return self.training_documentation

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

    def update_documentation_entry(self, entry, response_evaluation):
        self.training_documentation[entry]['lfd'] = str(date.today())
        self.training_documentation[entry]['tf'] += 1
        self.training_documentation[entry]['s'] += 0.5 if self.RESPONSE_EVALUATIONS[response_evaluation] in ['accent fault', 'correct'] else response_evaluation // 3

    def pre_training_display(self):
        self.clear_screen()
        n_imperfect_entries = len([e for e in self.training_documentation.values() if e['s'] < self.COMPLETION_SCORE])
        print(f'Vocabulary file comprises {n_imperfect_entries} entries.')

        lets_go_translation = self.get_lets_go_translation()
        print(lets_go_translation, '\n') if lets_go_translation is not None else print("Let's go!", '\n')

    def train(self):
        entries = np.array(list(self.vocabulary.keys()))
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

    def exit_screen(self):
        ratings = {0: 'You suck.',
                   20: 'Get your shit together m8.',
                   40: "You can't climb the ladder of success with your hands in your pockets.",
                   60: "Keep hustlin' young blood.",
                   80: 'Attayboy!',
                   100: '0361/2180494. Call me.'}

        percentage = int(self.n_correct_responses/self.n_trained * 100)
        print(f'You got {self.n_correct_responses}/{self.n_trained}, i.e. {percentage}% right', '\n')
        rating = ratings[percentage // 20 * 20]
        time.sleep(3)
        print(rating)

    def __get_root_comprising_tokens(self, root) -> List[str]:
        return [k for k in self.token_2_rowinds.keys() if root in k]

    def get_root_comprising_sentence_inds(self, root: str) -> List[int]:
        return list(chain.from_iterable([v for k, v in self.token_2_rowinds.items() if root in k]))

    def get_comprising_sentences(self, token: str) -> Optional[List[str]]:
        root = token[:self.ROOT_LENGTH]
        sentence_indices = np.array(self.get_root_comprising_sentence_inds(root))
        if not len(sentence_indices):
            return None

        random_indices = np.random.randint(0, len(sentence_indices), self.N_RELATED_SENTENCES)
        return self.sentence_data[sentence_indices[random_indices]][:, 1]

    def save_documentation(self):
        with open(self.training_documentation_path, 'w+') as dump_file:
            json.dump(self.training_documentation, dump_file)

    def run(self):
        self._language = self.select_language()
        self.sentence_data = self.parse_sentence_data()
        self.token_2_rowinds = self.procure_token_2_rowinds_map()
        self.vocabulary = self.parse_vocabulary()
        self.training_documentation = self.load_training_documentation()
        self.training_documentation = self.update_documentation()
        self.pre_training_display()
        self.train()
        self.save_documentation()
        self.exit_screen()


if __name__ == '__main__':
    VocabularyTrainer().run()

