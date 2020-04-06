from typing import List, Dict, Optional
import os
import json
from collections import Counter
from datetime import date

import unidecode
import numpy as np

from .trainer import Trainer


# TODO: query whether new vocabulary to be displayed

TrainingDocumentation = Dict[str, Dict[str, int]]  # entry -> Dict[score, times seen, last seen]


class VocabularyTrainer(Trainer):
    RESPONSE_EVALUATIONS = {0: 'wrong', 1: 'accent fault', 2: 'correct', 3: 'perfect'}

    def __init__(self):
        super().__init__()

        self.token_2_rowinds: Optional[Dict[str, List[int]]] = None
        self.training_documentation: Optional[TrainingDocumentation] = None
        self.vocabulary: Optional[Dict[str, str]] = None

        self.reference_2_foreign = True
        self.reverse_response_evaluations = {v: k for k, v in self.RESPONSE_EVALUATIONS.items()}

    @property
    def training_documentation_path(self):
        return f'{self.base_data_path}/{self.language}/vocabulary_training_documentation.json'

    def select_language(self) -> str:
        eligible_languages = [language for language in os.listdir(self.base_data_path) if 'vocabulary.txt' in os.listdir(f'{self.base_data_path}/{language}')]
        print('ELIGIBLE LANGUAGES: ')
        [print(language) for language in sorted(eligible_languages)]
        language_selection = input('\nEnter desired language:\n').title()
        if language_selection not in eligible_languages:
            return self.recurse_on_invalid_input(self.select_language)
        return language_selection

    def query_settings(self):
        pass

    def procure_word_2_rowinds_map(self) -> Dict[str, List[int]]:
        sentence_data = self.parse_sentence_data()
        token_2_rowinds = {}
        for i, sentence in enumerate(sentence_data[:, 1]):
            for token in sentence.split(' '):
                if token_2_rowinds.get(token) is None:
                    token_2_rowinds[token] = [i]
                else:
                    token_2_rowinds[token].append(i)
        return token_2_rowinds

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
            return {entry: INIT for entry in self.vocabulary.keys()}

        for entry in self.vocabulary.keys():
            if self.training_documentation.get(entry) is None:
                self.training_documentation[entry] = INIT
        return self.training_documentation

    def evaluate_response(self, response: str, translation: str) -> int:
        accent_pruned_translation = unidecode.unidecode(translation)

        def tolerable_error():
            def n_deviations(a: str, b: str) -> int:
                a_counter, b_counter = map(Counter, [a, b])
                return len(a_counter - b_counter) or len(a_counter - b_counter)
            TOLERATED_CHAR_DEVIATIONS = 1
            distinct_translations = accent_pruned_translation.split(',')
            return any(n_deviations(response, translation_token) <= TOLERATED_CHAR_DEVIATIONS for translation_token in distinct_translations)

        translation_tokens = translation.split(',')
        if response in translation_tokens:
            evaluation = 'perfect'
        elif response in accent_pruned_translation:
            evaluation = 'accent fault'
        elif tolerable_error():
            evaluation = 'correct'
        else:
            evaluation = 'wrong'
        return self.reverse_response_evaluations[evaluation]

    def _update_documentation_entry(self, entry, response_evaluation):
        self.training_documentation[entry]['lfd'] = date.today()
        self.training_documentation[entry]['tf'] += 1
        self.training_documentation[entry]['s'] = 0.5 if self.RESPONSE_EVALUATIONS[response_evaluation] in ['accent fault', 'correct'] else 3 // 1

    def train(self):
        entries = np.array(list(self.vocabulary.keys()))
        np.random.shuffle(entries)

        get_display_token = lambda entry: self.vocabulary[entry] if self.reference_2_foreign else entry
        get_translation = lambda entry: entry if self.reference_2_foreign else self.vocabulary[entry]

        for entry in entries:
            display_token, translation = get_display_token(entry), get_translation(entry)
            response = input(f'{display_token} : ')
            response_evaluation = self.evaluate_response(response, translation)
            if self.RESPONSE_EVALUATIONS[response_evaluation] != 'perfect':
                print(translation, end=' ')
            print(self.RESPONSE_EVALUATIONS[response_evaluation].title())
            self._update_documentation_entry(entry, response_evaluation)

    def run(self):
        self._language = self.select_language()
        self.token_2_rowinds = self.procure_word_2_rowinds_map()
        self.vocabulary = self.parse_vocabulary()
        self.training_documentation = self.load_training_documentation()
        self.training_documentation = self.update_documentation()
        self.train()


if __name__ == '__main__':
    VocabularyTrainer().run()

