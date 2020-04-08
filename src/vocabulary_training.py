from typing import List, Dict, Optional
import os
import json
from collections import Counter
from datetime import date
from itertools import chain
from time import time
from tqdm import tqdm

import unidecode
import numpy as np

from .trainer import Trainer


# TODO: query whether new vocabulary to be displayed

TrainingDocumentation = Dict[str, Dict[str, int]]  # entry -> Dict[score, times seen, last seen]
TokenSentenceindsMap = Dict[str, List[int]]


class VocabularyTrainer(Trainer):
    RESPONSE_EVALUATIONS = {0: 'wrong', 1: 'accent fault', 2: 'correct', 3: 'perfect'}
    COMPLETION_SCORE = 5
    N_RELATED_SENTENCES = 2
    ROOT_LENGTH = 4

    def __init__(self):
        super().__init__()

        self.token_2_rowinds: Optional[TokenSentenceindsMap] = None
        # self.root_2_rowinds: Optional[TokenSentenceindsMap] = None
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

    def procure_token_2_rowinds_map(self) -> TokenSentenceindsMap:
        token_2_rowinds = {}
        for i, sentence in enumerate(self.sentence_data[:, 1]):
            for token in sentence.split(' '):
                if token_2_rowinds.get(token) is None:
                    token_2_rowinds[token] = [i]
                else:
                    token_2_rowinds[token].append(i)
        return token_2_rowinds

    # def procure_root_2_rowinds_map(self) -> TokenSentenceindsMap:
    #     MIN_ROOT_LENGTH = 4
    #
    #     root_2_sentenceinds = {}
    #     token_2_rowinds = self.token_2_rowinds.copy()
    #
    #     while len(token_2_rowinds):
    #         token = next(iter(token_2_rowinds.keys()))
    #         root = token[:-self.ROOT_END_IND]
    #         if len(root) < MIN_ROOT_LENGTH:
    #             token_2_rowinds.pop(token)
    #         else:
    #             root_2_sentenceinds[root] = token_2_rowinds.pop(token)
    #             for c, c_inds in iter(token_2_rowinds.items()):
    #                 if root in c:
    #                     root_2_sentenceinds[root].extend(token_2_rowinds.pop(c))
    #
    #     return root_2_sentenceinds

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
        distinct_translations = translation.split(',')
        accent_pruned_translations = list(map(unidecode.unidecode, distinct_translations))

        def tolerable_error():
            def n_deviations(a: str, b: str) -> int:
                def dict_value_sum(dictionary):
                    return sum(list(dictionary.values()))
                ac, bc = map(Counter, [a, b])
                return dict_value_sum(ac - bc) or dict_value_sum(bc - ac)

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
        self.training_documentation[entry]['lfd'] = date.today()
        self.training_documentation[entry]['tf'] += 1
        self.training_documentation[entry]['s'] = 0.5 if self.RESPONSE_EVALUATIONS[response_evaluation] in ['accent fault', 'correct'] else 3 // 1

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
            response_evaluation = self.evaluate_response(response, translation)

            print('\t', self.RESPONSE_EVALUATIONS[response_evaluation].upper(), end=' ')
            if self.RESPONSE_EVALUATIONS[response_evaluation] != 'perfect':
                print(translation)
            comprising_sentences = self.get_comprising_sentences(entry.split(',')[0])
            if comprising_sentences is not None:
                [print(s) for s in comprising_sentences]
            print('_______________')

            self.update_documentation_entry(entry, response_evaluation)

    def get_root_comprising_tokens(self, root) -> List[str]:
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

    def run(self):
        self._language = self.select_language()
        self.sentence_data = self.parse_sentence_data()
        self.token_2_rowinds = self.procure_token_2_rowinds_map()
        self.vocabulary = self.parse_vocabulary()
        self.training_documentation = self.load_training_documentation()
        self.training_documentation = self.update_documentation()
        self.pre_training_display()
        self.train()


if __name__ == '__main__':
    VocabularyTrainer().run()

