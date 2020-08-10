from typing import *
from time import sleep

import numpy as np
import matplotlib.pyplot as plt
from pynput.keyboard import Controller as KeyboardController

from lingularity.frontend.console.trainers.base import TrainerConsoleFrontend
from lingularity.backend.trainers.vocabulary_trainer import VocabularyTrainerBackend
from lingularity.utils.output_manipulation import clear_screen, erase_lines
from lingularity.utils.input_resolution import resolve_input, recurse_on_unresolvable_input
from lingularity.utils.enum import ExtendedEnum


class VocableTrainerConsoleFrontend(TrainerConsoleFrontend):
    N_RELATED_SENTENCES_2_BE_DISPLAYED = 2

    def __init__(self):
        super().__init__()

        non_english_language, train_english = self._select_language()
        self._backend = VocabularyTrainerBackend(non_english_language, train_english)

    def run(self):
        self._display_new_vocabulary()
        self._display_pre_training_instructions()
        self._run_training()
        self._backend.insert_session_statistics_into_database(self._n_trained_items)
        self._display_pie_chart()
        self._plot_training_history()

    def _select_language(self) -> Tuple[str, bool]:
        eligible_languages = self._backend.get_vocabulary_possessing_languages()
        if not eligible_languages:
            self._start_sentence_translation_trainer()

        elif eligible_languages.__len__() == 1:
            return eligible_languages[0]

        print('ELIGIBLE LANGUAGES: ')
        for language in sorted(eligible_languages):
            print(language)

        language_selection = resolve_input(input('\nEnter desired language:\n').title(), eligible_languages)
        if language_selection is None:
            return recurse_on_unresolvable_input(self._select_language, deletion_lines=-1)
        return language_selection, True  # TODO

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

        lets_go_translation = self._backend.query_lets_go_translation()
        print(lets_go_translation, '\n') if lets_go_translation is not None else print("Let's go!", '\n')

    # ------------------
    # TRAINING
    # ------------------
    def _run_training(self):
        class Option(ExtendedEnum):
            AddMeaning = '#alter'
            Vocable = '#add'
            Exit = '#exit'

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