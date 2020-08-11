import time
from typing import Optional, Tuple
from itertools import groupby

from pynput.keyboard import Controller as KeyboardController

from lingularity.backend.trainers.sentence_translation import SentenceTranslationTrainerBackend as Backend
from lingularity.database import MongoDBClient
from lingularity.frontend.console.trainers.base import TrainerConsoleFrontend
from lingularity.utils.output_manipulation import (clear_screen, erase_lines, centered_print,
                                                   get_max_line_length_based_indentation, DEFAULT_VERTICAL_VIEW_OFFSET)
from lingularity.utils.input_resolution import resolve_input, recurse_on_unresolvable_input
from lingularity.utils.enum import ExtendedEnum


class SentenceTranslationTrainerConsoleFrontend(TrainerConsoleFrontend):
    def __init__(self, mongodb_client: MongoDBClient):
        super().__init__()

        non_english_language, train_english = self._select_language()
        training_mode = self._select_mode()

        self._backend = Backend(non_english_language, train_english, training_mode, mongodb_client)

    def run(self):
        self._display_pre_training_instructions()
        self._run_training()

        self._backend.insert_session_statistics_into_database(self._n_trained_items)
        self._plot_training_history()

    # ---------------
    # INITIALIZATION
    # ---------------
    def _select_language(self) -> Tuple[str, bool]:
        """
            Returns:
                non-english language: str
                train_english: bool """

        clear_screen()
        eligible_languages = Backend.get_eligible_languages()

        centered_print(f'{DEFAULT_VERTICAL_VIEW_OFFSET}Eligible languages:\n'.upper())
        starting_letter_grouped_languages = [', '.join(list(v)) for _, v in groupby(eligible_languages, lambda x: x[0])]
        indentation = get_max_line_length_based_indentation(starting_letter_grouped_languages)

        for language_group in starting_letter_grouped_languages:
            print(indentation, language_group)

        selection, train_english = resolve_input(input(f'{self.SELECTION_QUERY_OFFSET}Select language: ').title(), eligible_languages), False
        if selection is None:
            return recurse_on_unresolvable_input(self._select_language, deletion_lines=-1)

        elif selection == 'English':
            eligible_languages.remove('English')
            reference_language_validity = False

            while not reference_language_validity:
                reference_language = resolve_input(input('Enter desired reference language: \n\n').title(), eligible_languages)
                if reference_language is None:
                    print("Couldn't resolve input")
                    time.sleep(1)
                else:
                    selection = reference_language
                    train_english, reference_language_validity = [True]*2
        return selection, train_english

    # -----------------
    # .MODE
    # -----------------
    def _select_mode(self) -> str:
        explanations = (
            'show me sentences possessing an increased probability of containing rather infrequently used vocabulary',
            'show me sentences comprising exclusively commonly used vocabulary',
            'just hit me with dem sentences brah')

        clear_screen()
        indentation = get_max_line_length_based_indentation(explanations)

        centered_print(f'{DEFAULT_VERTICAL_VIEW_OFFSET}TRAINING MODES\n')
        for i in range(3):
            print(f'{indentation}{Backend.TrainingMode.values()[i].title()}:')
            print(f'{indentation}\t{explanations[i]}\n')

        mode_selection = resolve_input(input(f'{self.SELECTION_QUERY_OFFSET}Enter desired mode: ').lower(), Backend.TrainingMode.values())

        if mode_selection is None:
            return recurse_on_unresolvable_input(self._select_mode, deletion_lines=-1)
        print()
        return mode_selection

    def _display_pre_training_instructions(self):
        clear_screen()

        print((f"{DEFAULT_VERTICAL_VIEW_OFFSET * 2}Database comprises {self._backend.sentence_data_magnitude:,d} sentences.\n"
        "Hit Enter to advance to next sentence\n"
        "Enter \n"
            "\t- 'vocabulary' to append new entry to language specific vocabulary file\n" 
            "\t- 'exit' to terminate program\n"
            "\t- 'alter' in order to alter the most recently added vocable entry\n"))

        self._lets_go_output()

    # -----------------
    # Training
    # -----------------
    def _run_training(self):
        class Option(ExtendedEnum):
            Exit = 'exit'
            AppendVocabulary = 'vocabulary'
            AlterLatestVocableEntry = 'alter'

        suspend_resolution = False
        def maintain_resolution_suspension():
            nonlocal suspend_resolution
            print(" ")
            suspend_resolution = True

        def maintain_resolution_suspension_and_erase_lines(n_lines: int):
            maintain_resolution_suspension()
            erase_lines(n_lines)

        most_recent_vocable_entry: Optional[str] = None  # 'token - meaning'

        INDENTATION = '\t' * 2

        while True:
            if not suspend_resolution:
                try:
                    sentence_pair = self._backend.get_training_item()
                    if sentence_pair is None:
                        print('Sentence data file depleted')
                        return
                    reference_sentence, translation = self._backend.convert_names_if_possible(*sentence_pair)
                except (ValueError, IndexError):
                    continue


                self._buffer_print(INDENTATION, reference_sentence, '\t')
            else:
                suspend_resolution = False
            try:
                response = resolve_input(input("\t\tpending... ").lower(), Option.values())
                if response is not None:
                    if response == Option.AppendVocabulary.value:
                        most_recent_vocable_entry, n_printed_lines = self._insert_vocable_into_database()
                        maintain_resolution_suspension_and_erase_lines(n_lines=n_printed_lines+1)

                    elif response == Option.AlterLatestVocableEntry.value:
                        if most_recent_vocable_entry is None:
                            print("You haven't added any vocabulary during the current session")
                            time.sleep(1)
                            maintain_resolution_suspension_and_erase_lines(n_lines=2)
                        else:
                            altered_entry, n_printed_lines = self._modify_latest_vocable_insertion(most_recent_vocable_entry)
                            if altered_entry is not None:
                                most_recent_vocable_entry = altered_entry
                            maintain_resolution_suspension_and_erase_lines(n_lines=n_printed_lines)

                    elif response == Option.Exit.value:
                        print('\n----------------')
                        print("Number of faced sentences: ", self._n_trained_items)
                        return
            except (KeyboardInterrupt, SyntaxError):
                pass

            erase_lines(1)
            if not suspend_resolution:
                self._buffer_print(INDENTATION, translation, '\n', INDENTATION, '_______________')
                self._n_trained_items += 1

                if self._n_trained_items >= 5:
                    self._buffer_print.partially_redo_buffered_output(n_lines_to_be_removed=2)

    def _modify_latest_vocable_insertion(self, latest_appended_vocable_line: str) -> Tuple[Optional[str], int]:
        """ Returns:
                altered entry: str, None in case of invalid alteration
                n_printed_lines: int """

        old_token = latest_appended_vocable_line.split(' - ')[0]
        KeyboardController().type(f'{latest_appended_vocable_line}')
        new_entry = input('')
        new_split_entry = new_entry.split(' - ')
        if new_split_entry.__len__() == 1 or not all(new_split_entry):
            print('Invalid alteration')
            time.sleep(1)
            return None, 3

        assert self._backend is not None
        self._backend.mongodb_client.alter_vocable_entry(old_token, *new_split_entry)
        return new_entry, 2
