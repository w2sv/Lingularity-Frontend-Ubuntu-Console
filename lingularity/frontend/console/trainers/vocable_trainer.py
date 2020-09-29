from typing import Optional, Tuple
from time import sleep

import matplotlib.pyplot as plt
from pynput.keyboard import Controller as KeyboardController
import cursor

from lingularity.frontend.console.trainers import TrainerConsoleFrontend, SentenceTranslationTrainerConsoleFrontend
from lingularity.backend.trainers.vocable_trainer import VocableTrainerBackend as Backend, VocableEntry
from lingularity.backend.database import MongoDBClient
from lingularity.frontend.console.utils.output import (clear_screen, erase_lines, DEFAULT_VERTICAL_VIEW_OFFSET,
                                                       centered_print, get_max_line_length_based_indentation)
from lingularity.frontend.console.utils.input_resolution import resolve_input, recurse_on_unresolvable_input
from lingularity.backend.utils.enum import ExtendedEnum
from lingularity.frontend.console.utils.matplotlib import center_matplotlib_windows


class VocableTrainerConsoleFrontend(TrainerConsoleFrontend):
    def __init__(self, mongodb_client: MongoDBClient):
        super().__init__()

        self._accumulated_score = 0.0
        non_english_language, train_english = self._select_language(mongodb_client)

        cursor.hide()
        self._backend = Backend(non_english_language, train_english, mongodb_client)
        cursor.show()

    def _select_language(self, mongodb_client: Optional[MongoDBClient] = None) -> Tuple[str, bool]:
        if not (eligible_languages := Backend.get_eligible_languages(mongodb_client)):
            return self._start_sentence_translation_trainer()

        elif len(eligible_languages) == 1:
            return eligible_languages[0], False

        centered_print(DEFAULT_VERTICAL_VIEW_OFFSET, 'ELIGIBLE LANGUAGES', DEFAULT_VERTICAL_VIEW_OFFSET)

        indentation = get_max_line_length_based_indentation(eligible_languages)
        for language in sorted(eligible_languages):
            print(indentation, language)

        input_query_message = 'Enter desired language: '
        language_selection = resolve_input(f'\n{indentation[:-int(len(input_query_message) * 3/4)]}{input_query_message}', eligible_languages)
        if language_selection is None:
            return recurse_on_unresolvable_input(self._select_language, n_deletion_lines=-1)
        print('\n' * 2, end='')
        return language_selection, False  # TODO

    def _start_sentence_translation_trainer(self):
        print(DEFAULT_VERTICAL_VIEW_OFFSET)
        centered_print('You have to accumulate vocabulary by means of the SentenceTranslation™ TrainerBackend or manual amassment first.')
        sleep(3)
        centered_print('Initiating SentenceTranslation TrainerBackend...')
        sleep(2)
        clear_screen()
        return SentenceTranslationTrainerConsoleFrontend(self._backend.mongodb_client).run()

    # -----------------
    # Run
    # -----------------
    def run(self):
        self._backend.set_item_iterator()
        self._display_new_vocabulary()
        self._display_instructions()
        self._run_training()
        self._backend.enter_session_statistics_into_database(self._n_trained_items)
        self._display_pie_chart()
        self._plot_training_history()

    # -----------------
    # Pre training
    # -----------------
    def _display_new_vocabulary(self):
        clear_screen()
        new_vocabulary = self._backend.get_new_vocable_entries()
        if new_vocabulary:
            print(DEFAULT_VERTICAL_VIEW_OFFSET)
            centered_print('Would you like to see the vocabulary you recently added? (y)es/(n)o')
            centered_print(' ', end='')
            display_vocabulary = resolve_input('', ['yes', 'no'])
            if display_vocabulary == 'yes':
                [print('\t', entry.line_repr) for entry in new_vocabulary]
                print('\n')
                input('Press any key to continue')

    def _display_instructions(self):
        clear_screen()

        print(DEFAULT_VERTICAL_VIEW_OFFSET * 2)
        centered_print(f'Found {self._backend.n_training_items} imperfect entries.\n\n')
        between_instruction_indentation = ' ' * 2
        INSTRUCTIONS = ("Enter:",
                        f"{between_instruction_indentation}- '#alter' in order to alter the translation(s) of the previously faced item.",
                        f"{between_instruction_indentation * 4}Note: distinct translations are to be separated by commas.",
                        f"{between_instruction_indentation}- '#add' to add a new vocable.",
                        f"{between_instruction_indentation}- '#exit' to terminate the program.\n\n")

        indentation = get_max_line_length_based_indentation(INSTRUCTIONS)
        for instruction_row in INSTRUCTIONS:
            print(f'{indentation}{instruction_row}')

        self._output_lets_go()

    # ------------------
    # Training
    # ------------------
    def _run_training(self):
        INDENTATION = '\t' * 2

        class Option(ExtendedEnum):
            AddMeaning = '#alter'
            Vocable = '#add'
            Exit = '#exit'

        previous_entry: Optional[VocableEntry] = None

        while (entry := self._backend.get_training_item()) is not None:
            translation_query_output = f'{INDENTATION + entry.display_token} = '
            print(translation_query_output, end='')

            try:
                cursor.show()
                response = input()
                cursor.hide()
            except KeyboardInterrupt:
                print('')
                erase_lines(1)
                continue
            if response == Option.AddMeaning.value:
                cursor.show()
                n_printed_lines = self._alter_entry_translation(previous_entry)
                cursor.hide()
                erase_lines(n_printed_lines)
                continue
            elif response == Option.Vocable.value:
                cursor.show()
                _, n_printed_lines = self.get_new_vocable()
                cursor.hide()
                erase_lines(n_printed_lines + 1)
                continue
            elif response == Option.Exit.value:
                print('')
                erase_lines(2)
                break

            response_evaluation = self._backend.get_response_evaluation(response, entry.display_translation)
            entry.update_score(response_evaluation.value)
            self._backend.mongodb_client.update_vocable_entry(entry.token, entry.score)

            print('')
            erase_lines(2)
            print(f'{translation_query_output}{response} | {response_evaluation.name.upper()} {f"| Correct translation: {entry.display_translation}" if response_evaluation.name != "Perfect" else ""}{f" | New Score: {entry.score if entry.score % 1 != 0 else int(entry.score)}" if entry.score < 5 else "| Entry Perfected"}\n')

            if (related_sentence_pairs := self._backend.get_related_sentence_pairs(entry.display_translation, n=2)) is not None:
                forename_converted_sentence_pairs = [reversed(self._backend.forename_converter(sentence_pair)) for sentence_pair in related_sentence_pairs]
                joined_sentence_pairs = [' - '.join(sentence_pair) for sentence_pair in forename_converted_sentence_pairs]
                [centered_print(joined_sentence_pair) for joined_sentence_pair in joined_sentence_pairs]

            self._n_trained_items += 1
            self._accumulated_score += response_evaluation.value

            if not self._n_trained_items % 10 and self._n_trained_items != self._backend.n_training_items:
                centered_print(f'\n\n{self._n_trained_items} Entries faced, {self._backend.n_training_items - self._n_trained_items} more to go\n\n')
            else:
                centered_print('\n-----------------------\n')
            previous_entry = entry

    def _alter_entry_translation(self, entry: Optional[VocableEntry]) -> int:
        """ Returns:
                number of printed lines"""

        if not entry:
            return 1

        KeyboardController().type(entry.translation)
        extended_translation = input('')
        if extended_translation:
            self._backend.mongodb_client.insert_altered_vocable_entry(*[entry.token] * 2, extended_translation)  # type: ignore
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
        if int(self._accumulated_score) == self._accumulated_score:
            return int(self._accumulated_score)
        else:
            return self._accumulated_score

    @property
    def correctness_percentage(self) -> float:
        return self._accumulated_score / self._n_trained_items * 100

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
        center_matplotlib_windows()
        plt.show()