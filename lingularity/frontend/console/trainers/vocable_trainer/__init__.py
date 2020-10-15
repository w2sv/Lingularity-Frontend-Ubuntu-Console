from typing import Optional, Tuple
from time import sleep

import matplotlib.pyplot as plt

from lingularity.backend.database import MongoDBClient
from lingularity.backend.components import VocableEntry
from lingularity.backend.trainers.vocable_trainer import VocableTrainerBackend as Backend

from lingularity.frontend.console.trainers.vocable_trainer.options import *
from lingularity.frontend.console.trainers.sentence_translation import SentenceTranslationTrainerConsoleFrontend
from lingularity.frontend.console.trainers.base import TrainerConsoleFrontend
from lingularity.frontend.console.trainers.base.options import TrainingOptions
from lingularity.frontend.console.utils.view import view_creator, DEFAULT_VERTICAL_VIEW_OFFSET
from lingularity.frontend.console.utils.input_resolution import resolve_input, recurse_on_unresolvable_input
from lingularity.frontend.console.utils.matplotlib import center_matplotlib_windows
from lingularity.frontend.console.utils.output import (
    erase_lines,
    centered_print,
    centered_output_block_indentation
)


class VocableTrainerConsoleFrontend(TrainerConsoleFrontend):
    def __init__(self, mongodb_client: MongoDBClient):
        super().__init__(Backend, mongodb_client)

        self._accumulated_score = 0.0

        self._latest_faced_vocable_entry: Optional[VocableEntry] = None

    # -----------------
    # Driver
    # -----------------
    def __call__(self) -> bool:
        self._backend.set_item_iterator()
        self._display_new_vocabulary_if_applicable()

        self._display_training_screen_header()
        self._run_training()

        self._backend.enter_session_statistics_into_database(self._n_trained_items)
        self._display_pie_chart()
        self._plot_training_history()

        return False

    # -----------------
    # Training Options
    # -----------------
    def _get_training_options(self) -> TrainingOptions:
        VocableTrainerOption.set_frontend_instance(self)
        return TrainingOptions([AddVocable, AlterLatestCreatedVocableEntry, AlterLatestFacedVocableEntry, Exit])

    # -----------------
    # Training Property Selection
    # -----------------
    @view_creator
    def _select_training_language(self, mongodb_client: Optional[MongoDBClient] = None) -> Tuple[str, bool]:
        assert mongodb_client is not None

        if not (eligible_languages := Backend.get_eligible_languages(mongodb_client)):
            return self._start_sentence_translation_trainer(mongodb_client)

        elif len(eligible_languages) == 1:
            return eligible_languages[0], False

        centered_print('ELIGIBLE LANGUAGES', DEFAULT_VERTICAL_VIEW_OFFSET)

        indentation = centered_output_block_indentation(eligible_languages)
        for language in sorted(eligible_languages):
            print(indentation, language)

        input_query_message = 'Enter desired language: '
        language_selection = resolve_input(input(f'\n{indentation[:-int(len(input_query_message) * 3/4)]}{input_query_message}'), eligible_languages)
        if language_selection is None:
            return recurse_on_unresolvable_input(self._select_training_language, -1, args=(mongodb_client, ))
        print('\n' * 2, end='')

        return language_selection, False  # TODO

    @staticmethod
    @view_creator
    def _start_sentence_translation_trainer(mongodb_client: MongoDBClient):
        centered_print('You have to accumulate vocabulary by means of the SentenceTranslation™ TrainerBackend or manual amassment first.')
        sleep(3)
        centered_print('Initiating SentenceTranslation TrainerBackend...')
        sleep(2)
        return SentenceTranslationTrainerConsoleFrontend(mongodb_client).__call__()

    # -----------------
    # Pre Training
    # -----------------
    @view_creator
    def _display_new_vocabulary_if_applicable(self):
        if (new_vocabulary := self._backend.get_new_vocable_entries()) is None:
            return

        centered_print('Would you like to see the vocabulary you recently added? (y)es/(n)o')
        centered_print(' ', end='')
        display_vocabulary = resolve_input(input(''), ['yes', 'no'])
        if display_vocabulary == 'yes':
            [print('\t', entry.line_repr) for entry in new_vocabulary]
            input('\n\nPress any key to continue')

    @view_creator
    def _display_training_screen_header(self):
        centered_print(f'Found {self._backend.n_training_items} imperfect entries.\n\n')

        instructions = ["Enter: "] + self._training_options.instructions

        indentation = centered_output_block_indentation(instructions)
        for i, instruction_row in enumerate(instructions):
            print(f'{indentation}{instruction_row}')
            if i == 3:
                print(f"{indentation}\t\tNote: distinct translations are to be separated by commas")

        print('')
        self._output_lets_go()

    # ------------------
    # Training
    # ------------------
    def _run_training(self):
        INDENTATION = '\t' * 2

        entry: VocableEntry = self._backend.get_training_item()

        while entry is not None:
            translation_query_output = f'{INDENTATION + entry.display_token} = '
            print(translation_query_output, end='')

            response = input()
            if (option_selection := resolve_input(response, self._training_options.keywords)) is not None:
                self._training_options[option_selection].execute()
                if type(self._training_options[option_selection]) is Exit:
                    return

            else:
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
                self._latest_faced_vocable_entry = entry

                if not self._n_trained_items % 10 and self._n_trained_items != self._backend.n_training_items:
                    centered_print(f'\n\n{self._n_trained_items} Entries faced, {self._backend.n_training_items - self._n_trained_items} more to go\n\n')
                else:
                    centered_print('\n-----------------------\n')

                entry = self._backend.get_training_item()

    # -----------------
    # Post Training
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

        CENT = 100

        correct_percentage = (self.n_correct_responses / self._n_trained_items) * CENT
        incorrect_percentage = CENT - correct_percentage

        labels = ['Correct', 'Incorrect']
        explode = (0.1, 0)
        sizes = correct_percentage, incorrect_percentage
        colors = ['g', 'r']
        try:
            def discard_futile_value(*iterables):
                hundred_percent_index = [correct_percentage, incorrect_percentage].index(CENT)
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
