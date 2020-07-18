from typing import List, Dict, Optional, Union
from collections import Counter
from time import sleep

import unidecode
import numpy as np
import matplotlib.pyplot as plt

from lingularity.trainers import Trainer
from lingularity.trainers.sentence_translation import SentenceTranslationTrainer
from lingularity.types.token_maps import RawToken2SentenceIndices
from lingularity import database
from lingularity.utils.strings import get_article_stripped_token
from lingularity.utils.output_manipulation import clear_screen
from lingularity.utils.input_resolution import resolve_input, recurse_on_invalid_input
from lingularity.utils.enum import ExtendedEnum


class VocabularyTrainer(Trainer):
    class ResponseEvaluation(ExtendedEnum):
        Wrong = 0
        AccentError = 0.5
        AlmostCorrect = 0.5
        Perfect = 1

    class VocableEntry:
        Type = Dict[str, Dict[str, Union[float, str, int]]]
        REFERENCE_TO_FOREIGN = None

        def __init__(self, entry: Type):
            self._entry = entry

        @property
        def token(self) -> str:
            return next(iter(self._entry.keys()))

        @property
        def display_token(self) -> str:
            return self.translation if not self.REFERENCE_TO_FOREIGN else self.token

        @property
        def translation(self) -> str:
            return self._entry[self.token]['translation']

        @property
        def display_translation(self) -> str:
            return self.translation if self.REFERENCE_TO_FOREIGN else self.token

        @property
        def last_faced_date(self) -> Optional[str]:
            return self._entry[self.token]['lfd']

        def __str__(self):
            return str(self._entry)

    N_RELATED_SENTENCES = 2
    ROOT_LENGTH = 4

    def __init__(self):
        super().__init__()

        self._reference_2_foreign = False  # TODO: make alterable

        self._sentence_data = self._parse_sentence_data()
        self._token_2_rowinds = RawToken2SentenceIndices(self._sentence_data)
        self._vocable_entries: List[VocabularyTrainer.VocableEntry] = self._get_vocable_entries()

        self._n_correct_responses = 0

    def run(self):
        self._display_new_vocabulary()
        self._display_pre_training_instructions()
        self._train()
        self._append_session_statistics_to_training_history()
        self._display_pie_chart()
        self._plot_training_history()

    def _get_vocable_entries(self) -> List[VocableEntry]:
        self.VocableEntry.REFERENCE_TO_FOREIGN = self._reference_2_foreign
        return list(map(self.VocableEntry, self._database_client.query_vocabulary_data()))

    # ---------------
    # INITIALIZATION
    # ---------------
    def _select_language(self) -> str:
        eligible_languages = database.MongoDBClient('janek_zangenberg', None, database.Credentials.default()).get_vocabulary_possessing_languages()
        if not eligible_languages:
            self._start_sentence_translation_trainer()

        print('ELIGIBLE LANGUAGES: ')
        for language in sorted(eligible_languages):
            print(language)
        language_selection = input('\nEnter desired language:\n').title()
        input_resolution = resolve_input(language_selection, eligible_languages)
        if input_resolution is None:
            return recurse_on_invalid_input(self._select_language)
        return input_resolution

    @staticmethod
    def _start_sentence_translation_trainer():
        print('You have to accumulate vocabulary by means of the SentenceTranslation™ Trainer or manual amassment first.')
        sleep(3)
        print('Initiating SentenceTranslation Trainer...')
        sleep(2)
        clear_screen()
        return SentenceTranslationTrainer().run()

    def _display_new_vocabulary(self):
        clear_screen()
        display_vocabulary = resolve_input(input('Do you want new vocabulary to be displayed once before training? (y)es/(n)o\n').lower(), ['yes', 'no'])
        if display_vocabulary == 'yes':
            new_vocabulary = [entry for entry in self._vocable_entries if entry.last_faced_date is None]
            if not new_vocabulary:
                return
            [print('\t', ' - '.join([entry.token, entry.translation])) for entry in new_vocabulary]
            print('\n')
            input('Press any key to continue')

    def _display_pre_training_instructions(self):
        clear_screen()

        print((f'Found {self._vocable_entries.__len__()} imperfect entries.\n'
                "Enter: \n\t- 'add' + meaning(s) in order to add to the ones of the previously faced item.\n"
                "\t\tNote: distinct newly entered translation tokens are to be separated by commas.\n"
                "\t- 'exit' to terminate the program.\n\n"))

        lets_go_translation = self._find_lets_go_translation()
        print(lets_go_translation, '\n') if lets_go_translation is not None else print("Let's go!", '\n')

    # ------------------
    # TRAINING
    # ------------------
    def _append_translation(self, entry: str, additional_translations: str):
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

    def _train(self):
        class Option(ExtendedEnum):
            Exit = 'exit'
            AppendMeaning = 'append'

        np.random.shuffle(self._vocable_entries)

        i, display_item = 0, True
        while i < len(self._vocable_entries):
            entry = self._vocable_entries[i]
            print(f'{entry.display_token} = ', end='') if display_item else print('Enter translation: ', end='')

            try:
                response = input()
            except KeyboardInterrupt:
                display_item = False
                continue
            if response == Option.Exit.value:
                break
            elif response == Option.AppendMeaning.value:
                # TODO
                display_item = False
                continue

            response_evaluation = self._get_reponse_evaluation(response, entry.display_translation)
            self._database_client.update_vocable_entry(entry.token, response_evaluation.value)

            print('\t', response_evaluation.name, end=' ')
            if response_evaluation != self.ResponseEvaluation.Perfect:
                print('| Correct translation: ', entry.display_translation, end='')
            print('')
            comprising_sentences = self._get_related_sentences(entry.display_translation)
            if comprising_sentences is not None:
                [print('\t', s) for s in comprising_sentences]
            print('_______________')

            self._n_trained_items += 1
            self._n_correct_responses += response_evaluation.value

            if i and not i % 9:
                print(f'{i} Entries faced, {len(self._vocable_entries) - i} more to go', '\n')

            i += 1
            display_item = True

    def _get_reponse_evaluation(self, response: str, translation: str) -> ResponseEvaluation:
        distinct_translations = translation.split(',')
        accent_pruned_translations = list(map(unidecode.unidecode, distinct_translations))

        def tolerable_error():
            def n_deviations(a: str, b: str) -> int:
                def dict_value_sum(dictionary):
                    return sum(list(dictionary.values()))
                short, long = sorted([a, b], key=lambda string: len(string))
                short_c, long_c = map(Counter, [short, long])  # type: ignore
                return dict_value_sum(long_c - short_c)

            TOLERATED_CHAR_DEVIATIONS = 1
            return any(n_deviations(response, translation) <= TOLERATED_CHAR_DEVIATIONS for translation in distinct_translations)

        if response in translation.split(','):
            return self.ResponseEvaluation.Perfect

        elif response in accent_pruned_translations:
            return self.ResponseEvaluation.AccentError

        elif tolerable_error():
            return self.ResponseEvaluation.AlmostCorrect

        else:
            return self.ResponseEvaluation.Wrong

    def _get_related_sentences(self, token: str) -> Optional[List[str]]:
        root = get_article_stripped_token(token)[:self.ROOT_LENGTH]
        sentence_indices = np.asarray(self._token_2_rowinds.get_root_comprising_sentence_indices(root))
        if not len(sentence_indices):
            return None

        random_indices = np.random.randint(0, len(sentence_indices), self.N_RELATED_SENTENCES)
        return self._sentence_data[sentence_indices[random_indices]][:, 1]

    # -----------------
    # PROGRAM TERMINATION
    # -----------------
    @property
    def correctness_percentage(self) -> float:
        return self._n_correct_responses / self._n_trained_items * 100

    @property
    def performance_verdict(self) -> str:
        return {
            0: 'You suck.',
            20: 'Get your shit together m8.',
            40: "You can't climb the ladder of success with your hands in your pockets.",
            60: "Keep hustlin' young blood.",
            80: 'Attayboy!',
            100: '0361/2680494. Call me.'}[int(self.correctness_percentage) // 20 * 20]

    def _display_pie_chart(self):
        if not self._n_trained_items:
            return
        correct_percentage = (self._n_correct_responses / self._n_trained_items) * 100
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
        fig.canvas.set_window_title(f'You got {self._n_correct_responses}/{self._n_trained_items} right')
        plt.show()


if __name__ == '__main__':
    VocabularyTrainer().run()
