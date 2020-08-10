from typing import List, Dict, Optional, Any
from collections import Counter
from time import sleep

import unidecode
import numpy as np
import matplotlib.pyplot as plt
from pynput.keyboard import Controller as KeyboardController

from lingularity.backend.trainers.base import TrainerBackend
from lingularity.backend.types.token_maps import RawToken2SentenceIndices
from lingularity.database import MongoDBClient
from lingularity.utils.strings import get_article_stripped_token
from lingularity.utils.output_manipulation import clear_screen, erase_lines
from lingularity.utils.input_resolution import resolve_input, recurse_on_unresolvable_input
from lingularity.utils.enum import ExtendedEnum


class VocabularyTrainerBackend(TrainerBackend):
    class ResponseEvaluation(ExtendedEnum):
        Wrong = 0
        AccentError = 0.5
        AlmostCorrect = 0.5
        Perfect = 1

    class VocableEntry:
        RawType = Dict[str, Dict[str, Any]]
        REFERENCE_TO_FOREIGN: Optional[bool] = None

        def __init__(self, entry: RawType):
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

    def __init__(self, database_client: MongoDBClient):
        super().__init__(database_client)

        self._reference_2_foreign = False  # TODO: make alterable

        self._sentence_data = self._parse_sentence_data()
        self._token_2_rowinds = RawToken2SentenceIndices(self._sentence_data, language=self.language)
        self._vocable_entries: List[VocabularyTrainerBackend.VocableEntry] = self._get_vocable_entries()

        self._n_correct_responses = 0

    def run(self):
        self._display_new_vocabulary()
        self._display_pre_training_instructions()
        self._train()
        self.insert_session_statistics_into_database()
        self._display_pie_chart()
        self._plot_training_history()

    # ---------------
    # INITIALIZATION
    # ---------------
    def _select_language(self) -> str:
        eligible_languages = self.mongodb_client.get_vocabulary_possessing_languages()
        if not eligible_languages:
            self._start_sentence_translation_trainer()

        elif eligible_languages.__len__() == 1:
            return eligible_languages[0]

        print('ELIGIBLE LANGUAGES: ')
        for language in sorted(eligible_languages):
            print(language)
        language_selection = input('\nEnter desired language:\n').title()
        input_resolution = resolve_input(language_selection, eligible_languages)
        if input_resolution is None:
            return recurse_on_unresolvable_input(self._select_language, deletion_lines=-1)
        return input_resolution

    def _get_vocable_entries(self) -> List[VocableEntry]:
        self.VocableEntry.REFERENCE_TO_FOREIGN = self._reference_2_foreign
        return list(map(self.VocableEntry, self.mongodb_client.query_vocabulary_data()))

    def _start_sentence_translation_trainer(self):
        print('You have to accumulate vocabulary by means of the SentenceTranslation™ TrainerBackend or manual amassment first.')
        sleep(3)
        print('Initiating SentenceTranslation TrainerBackend...')
        sleep(2)
        clear_screen()
        return SentenceTranslationTrainerBackend(self.mongodb_client).run()

    def _display_new_vocabulary(self):
        clear_screen()
        new_vocabulary = [entry for entry in self._vocable_entries if entry.last_faced_date is None]
        if new_vocabulary:
            display_vocabulary = resolve_input(input('Would you like to see the vocabulary you recently added? (y)es/(n)o\n').lower(), ['yes', 'no'])
            if display_vocabulary == 'yes':
                [print('\t', ' - '.join([entry.token, entry.translation])) for entry in new_vocabulary]
                print('\n')
                input('Press any key to continue')

    def _display_pre_training_instructions(self):
        clear_screen()

        print((f'Found {self._vocable_entries.__len__()} imperfect entries.\n'
                "Enter: \n\t- '#alter' in order to alter the translation(s) of the previously faced item.\n"
                "\t\tNote: distinct translations are to be separated by commas.\n"
                "\t- '#add' to add a new vocable.\n"
                "\t- '#exit' to terminate the program.\n\n"))

        lets_go_translation = self.query_lets_go_translation()
        print(lets_go_translation, '\n') if lets_go_translation is not None else print("Let's go!", '\n')

    # ------------------
    # TRAINING
    # ------------------
    def _train(self):
        class Option(ExtendedEnum):
            AddMeaning = '#alter'
            Vocable = '#add'
            Exit = '#exit'

        np.random.shuffle(self._vocable_entries)

        previous_entry: Optional[VocabularyTrainerBackend.VocableEntry] = None

        while self._n_trained_items < len(self._vocable_entries):
            entry = self._vocable_entries[self._n_trained_items]
            print(f'{entry.display_token} = ', end='')

            try:
                response = input()
            except KeyboardInterrupt:
                print('')
                erase_lines(1)
                continue
            if response == Option.AddMeaning.value:
                n_printed_lines = self._alter_entry_translation(previous_entry)
                erase_lines(n_printed_lines)
                continue
            elif response == Option.Vocable.value:
                _, n_printed_lines = self._insert_vocable_into_database()
                erase_lines(n_printed_lines + 1)
                continue
            elif response == Option.Exit.value:
                erase_lines(1)
                break

            response_evaluation = self._get_reponse_evaluation(response, entry.display_translation)
            self.mongodb_client.update_vocable_entry(entry.token, response_evaluation.value)

            if response:
                print('\t', response_evaluation.name, end=' ')
            if response_evaluation != self.ResponseEvaluation.Perfect:
                print(f'{"| " if response else "         "}Correct translation: ', entry.display_translation, end='')
            print('')
            related_sentences = self._get_related_sentences(entry.display_translation)
            if related_sentences is not None:
                if self._names_convertible:
                    related_sentences = map(self._accommodate_names_of_sentence, related_sentences)
                [print('\t', s) for s in related_sentences]
            print('_______________')

            self._n_trained_items += 1
            self._n_correct_responses += response_evaluation.value

            if not self._n_trained_items % 10 and self._n_trained_items != len(self._vocable_entries):
                print(f'\t\t{self._n_trained_items} Entries faced, {len(self._vocable_entries) - self._n_trained_items} more to go', '\n')

            previous_entry = entry

    def _alter_entry_translation(self, entry: Optional[VocableEntry]) -> int:
        """ Returns:
                number of printed lines"""

        if not entry:
            return 1
        KeyboardController().type(entry.translation)
        extended_translation = input('')
        if extended_translation:
            self.mongodb_client.alter_vocable_entry(*[entry.token] * 2, extended_translation)  # type: ignore
            return 2
        else:
            print('Invalid input')
            sleep(1)
            return 2

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
        WORD_ROOT_LENGTH = 4

        root = get_article_stripped_token(token)[:WORD_ROOT_LENGTH]
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
