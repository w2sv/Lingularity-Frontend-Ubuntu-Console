from typing import *
from time import sleep

import matplotlib.pyplot as plt
from pynput.keyboard import Controller as KeyboardController

from lingularity.frontend.console.trainers import TrainerConsoleFrontend, SentenceTranslationTrainerConsoleFrontend
from lingularity.backend.trainers.vocable_trainer import VocableTrainerBackend, VocableEntry
from lingularity.database import MongoDBClient
from lingularity.utils.output_manipulation import clear_screen, erase_lines
from lingularity.utils.input_resolution import resolve_input, recurse_on_unresolvable_input
from lingularity.utils.enum import ExtendedEnum


class VocableTrainerConsoleFrontend(TrainerConsoleFrontend):
    N_RELATED_SENTENCES_2_BE_DISPLAYED = 2

    def __init__(self, mongodb_client: MongoDBClient, vocable_expansion_mode=False):
        super().__init__()

        self._n_correct_responses = 0

        self._temp_mongodb_client = mongodb_client
        non_english_language, train_english = self._select_language()
        del self._temp_mongodb_client

        self._backend = VocableTrainerBackend(non_english_language, train_english, mongodb_client, vocable_expansion_mode)

    def _select_language(self) -> Tuple[str, bool]:
        if not (eligible_languages:= self._temp_mongodb_client.get_vocabulary_possessing_languages()):
            self._start_sentence_translation_trainer()

        elif eligible_languages.__len__() == 1:
            return eligible_languages[0], False

        print('ELIGIBLE LANGUAGES: ')
        for language in sorted(eligible_languages):
            print(language)

        language_selection = resolve_input(input('\nEnter desired language:\n').title(), eligible_languages)
        if language_selection is None:
            return recurse_on_unresolvable_input(self._select_language, deletion_lines=-1)
        return language_selection, False  # TODO

    def _start_sentence_translation_trainer(self):
        print('You have to accumulate vocabulary by means of the SentenceTranslation™ TrainerBackend or manual amassment first.')
        sleep(3)
        print('Initiating SentenceTranslation TrainerBackend...')
        sleep(2)
        clear_screen()
        return SentenceTranslationTrainerConsoleFrontend(self._backend.mongodb_client).run()

    # -----------------
    # Run
    # -----------------
    def run(self):
        self._display_new_vocabulary()
        self._display_pre_training_instructions()
        self._run_training()
        self._backend.insert_session_statistics_into_database(self._n_trained_items)
        self._display_pie_chart()
        self._plot_training_history()

    # -----------------
    # Pre training
    # -----------------
    def _display_new_vocabulary(self):
        clear_screen()
        new_vocabulary = self._backend.get_new_vocable_entries()
        if new_vocabulary:
            display_vocabulary = resolve_input(input('Would you like to see the vocabulary you recently added? (y)es/(n)o\n').lower(), ['yes', 'no'])
            if display_vocabulary == 'yes':
                [print('\t', entry.line_repr) for entry in new_vocabulary]
                print('\n')
                input('Press any key to continue')

    def _display_pre_training_instructions(self):
        clear_screen()

        print((f'Found {self._backend.n_imperfect_vocable_entries} imperfect entries.\n'
                "Enter: \n\t- '#alter' in order to alter the translation(s) of the previously faced item.\n"
                "\t\tNote: distinct translations are to be separated by commas.\n"
                "\t- '#add' to add a new vocable.\n"
                "\t- '#exit' to terminate the program.\n\n"))

        self._lets_go_output()

    # ------------------
    # Training
    # ------------------
    def _run_training(self):
        class Option(ExtendedEnum):
            AddMeaning = '#alter'
            Vocable = '#add'
            Exit = '#exit'

        previous_entry: Optional[VocableEntry] = None

        while (entry := self._backend.get_training_item()) is not None:
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
                _, n_printed_lines = self.insert_vocable_into_database()
                erase_lines(n_printed_lines + 1)
                continue
            elif response == Option.Exit.value:
                erase_lines(1)
                break

            response_evaluation = self._backend.get_response_evaluation(response, entry.display_translation)
            self._backend.mongodb_client.update_vocable_entry(entry.token, response_evaluation.value)

            if response:
                print('\t', response_evaluation.name, end=' ')
            if response_evaluation != self._backend.ResponseEvaluation.Perfect:
                print(f'{"| " if response else "         "}Correct translation: ', entry.display_translation, end='')
            print('')

            related_sentences = self._backend.get_related_sentences(entry.display_translation, n=self.N_RELATED_SENTENCES_2_BE_DISPLAYED)
            if related_sentences is not None:
                if self._backend.names_convertible:
                    related_sentences = map(self._backend.accommodate_names, related_sentences)
                [print('\t', s) for s in related_sentences]
            print('_______________')

            self._n_trained_items += 1
            self._n_correct_responses += response_evaluation.value

            if not self._n_trained_items % 10 and self._n_trained_items != self._backend.n_imperfect_vocable_entries:
                print(f'\t\t{self._n_trained_items} Entries faced, {self._backend.n_imperfect_vocable_entries - self._n_trained_items} more to go', '\n')

            previous_entry = entry

    def _alter_entry_translation(self, entry: Optional[VocableEntry]) -> int:
        """ Returns:
                number of printed lines"""

        if not entry:
            return 1
        KeyboardController().type(entry.translation)
        extended_translation = input('')
        if extended_translation:
            self._backend.mongodb_client.alter_vocable_entry(*[entry.token] * 2, extended_translation)  # type: ignore
            return 2
        else:
            print('Invalid input')
            sleep(1)
            return 2

    # -----------------
    # Post training
    # -----------------
    @property
    def n_correct_responses(self) -> float:
        if int(self._n_correct_responses) == self._n_correct_responses:
            return int(self._n_correct_responses)
        else:
            return self._n_correct_responses

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

        correct_percentage = (self.n_correct_responses / self._n_trained_items) * 100
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
        fig.canvas.set_window_title(f'You got {self.n_correct_responses}/{self._n_trained_items} right')
        plt.show()