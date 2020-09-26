import time
from typing import Optional, Tuple
from itertools import groupby
import os
from functools import partial

from pynput.keyboard import Controller as KeyboardController
import cursor

from lingularity.backend.trainers.sentence_translation import SentenceTranslationTrainerBackend as Backend
from lingularity.backend.database import MongoDBClient
from lingularity.frontend.console.trainers.base import TrainerConsoleFrontend
from lingularity.frontend.console.utils.output_manipulation import (clear_screen, erase_lines, centered_print,
                                                                    get_max_line_length_based_indentation,
                                                                    DEFAULT_VERTICAL_VIEW_OFFSET)
from lingularity.frontend.console.utils.input_resolution import (resolve_input, recurse_on_unresolvable_input,
                                                                 recurse_on_invalid_input)
from lingularity.backend.utils.enum import ExtendedEnum


class SentenceTranslationTrainerConsoleFrontend(TrainerConsoleFrontend):
    def __init__(self, mongodb_client: MongoDBClient):
        super().__init__()

        non_english_language, train_english = self._select_language()
        training_mode = self._select_mode()
        cursor.hide()

        self._backend = Backend(non_english_language, train_english, training_mode, mongodb_client)

        self._tts_enabled = True
        self._playback_speed = self._get_playback_speed()

        self._training_loop_suspended = False
        self._most_recent_vocable_entry_line_repr: Optional[str] = None  # 'token - meaning'
        self._audio_file_path: Optional[str] = None

    def _get_playback_speed(self) -> Optional[float]:
        assert self._backend is not None

        if not self._backend.tts_available:
            return None
        else:
            if (preset_playback_speed := self._backend.mongodb_client.query_playback_speed()) is not None:
                return preset_playback_speed
            else:
                return 1.0

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

        selection, train_english = resolve_input(input(f'{self.SELECTION_QUERY_OUTPUT_OFFSET}Select language: ').title(), eligible_languages), False
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

    def _select_mode(self) -> str:
        explanations = (
            'show me sentences containing rather infrequently used vocabulary',
            'show me sentences comprising exclusively commonly used vocabulary',
            'just hit me with dem sentences')

        clear_screen()
        indentation = get_max_line_length_based_indentation(explanations)

        centered_print(f'{DEFAULT_VERTICAL_VIEW_OFFSET}TRAINING MODES\n')
        for i in range(3):
            print(f'{indentation}{Backend.TrainingMode.values()[i].title()}:')
            print(f'{indentation}\t{explanations[i]}\n')

        mode_selection = resolve_input(input(f'{self.SELECTION_QUERY_OUTPUT_OFFSET}Enter desired mode: ').lower(), Backend.TrainingMode.values())

        if mode_selection is None:
            return recurse_on_unresolvable_input(self._select_mode, deletion_lines=-1)

        print('\n', end='')
        return mode_selection

    # -----------------
    # Driver
    # -----------------
    def run(self):
        self._display_pre_training_instructions()
        self._run_training()

        self._backend.insert_session_statistics_into_database(self._n_trained_items)
        self._plot_training_history()

    # -----------------
    # Pre training
    # -----------------
    def _display_pre_training_instructions(self):
        clear_screen()
        centered_print(f"{DEFAULT_VERTICAL_VIEW_OFFSET * 2}Document comprises {self._backend.sentence_data_magnitude:,d} sentences.\n\n")

        explanations = (
            'add a vocable',
            'alter the most recently added vocable entry',
            'to terminate program\n',
            'enable speech output',
            'disable speech output',
            'change playback speed')

        instructions = (
            "Hit Enter to advance to next sentence",
            "Enter",
            *[f"\t- '{option.value}' to {explanations[i]}" for i, option in enumerate(self.TrainingOption)])

        if not self._backend.tts_available:
            instructions = instructions[:-3]

        indentation = get_max_line_length_based_indentation(instructions)
        for line in instructions:
            print(indentation, line)

        print('\n' * 2, end='')
        self._output_lets_go()

    # -----------------
    # Training
    # -----------------
    @property
    def _tts_available_and_enabled(self) -> bool:
        assert self._backend is not None

        return self._backend.tts_available and self._tts_enabled

    def _remove_audio_file(self):
        os.remove(self._audio_file_path)
        self._audio_file_path = None

    class TrainingOption(ExtendedEnum):
        AddVocabulary = 'vocabulary'
        AlterLatestVocableEntry = 'alter'
        Exit = 'exit'

        EnableTTS = 'enable'
        DisableTTS = 'disable'
        ChangePlaybackSpeed = 'change'

    def _run_training(self):
        translation: Optional[str] = None

        INDENTATION = ' ' * 16

        while True:
            if not self._training_loop_suspended:
                # get sentence pair
                if (sentence_pair := self._backend.get_training_item()) is None:
                    print('\nSentence data file depleted')
                    return

                # try to convert forenames, output reference language sentence
                reference_sentence, translation = self._backend.convert_sentences_forenames_if_feasible(sentence_pair)
                self._buffer_print(f'{INDENTATION}{reference_sentence}')
                print(f"{INDENTATION}pending... ")

            # get tts audio file if available
            if self._tts_available_and_enabled and self._audio_file_path is None:
                self._audio_file_path = self._backend.download_tts_audio(text=translation)

            self._training_loop_suspended = False

            # get response, execute selected option if applicable
            if (response := resolve_input(input('$').lower(), options=self.TrainingOption.values())) is not None:
                exit_training = self._execute_option(option=self.TrainingOption(response))
                if exit_training:
                    return

            if not self._training_loop_suspended:
                # erase pending... + entered option identifier
                erase_lines(2)

                # output translation
                self._buffer_print(f'{INDENTATION}{translation}')
                self._buffer_print(f'{INDENTATION}_______________')

                # play tts file if available, otherwise suspend program
                # for some time to incentivise gleaning over translation
                if self._tts_available_and_enabled:
                    self._backend.play_audio_file(self._audio_file_path, self._playback_speed, suspend_program_for_duration=True)
                    self._remove_audio_file()
                else:
                    time.sleep(len(translation) * 0.05)

                self._n_trained_items += 1

                if self._n_trained_items >= 5:
                    self._buffer_print.partially_redo_buffered_output(n_lines_to_be_removed=3)

    def _execute_option(self, option: TrainingOption) -> bool:
        """ Returns:
                exit_training flag """

        assert self._backend is not None

        def suspend_training_loop(n_lines_to_be_erased: int):
            self._training_loop_suspended = True
            erase_lines(n_lines_to_be_erased)

        if option is self.TrainingOption.AddVocabulary:
            self._most_recent_vocable_entry_line_repr, n_printed_lines = self.insert_vocable_into_database()
            suspend_training_loop(n_lines_to_be_erased=n_printed_lines + 1)

        elif option is self.TrainingOption.AlterLatestVocableEntry:
            if self._most_recent_vocable_entry_line_repr is None:
                print("You haven't added any vocabulary during the current session")
                time.sleep(1)
                suspend_training_loop(n_lines_to_be_erased=1)
            else:
                altered_entry, n_printed_lines = self._modify_latest_vocable_insertion(self._most_recent_vocable_entry_line_repr)
                if altered_entry is not None:
                    self._most_recent_vocable_entry_line_repr = altered_entry
                suspend_training_loop(n_lines_to_be_erased=n_printed_lines)

        elif option is self.TrainingOption.Exit:
            self._backend.clear_tts_audio_file_dir()
            erase_lines(1)
            print(f'\nNumber of faced sentences: {self._n_trained_items}')
            cursor.show()
            return True

        elif not self._backend.tts_available:
            return False

        # ----------------
        # TTS Options
        # ----------------
        elif option is self.TrainingOption.DisableTTS and self._tts_enabled:
            self._remove_audio_file()
            self._tts_enabled = False
            suspend_training_loop(n_lines_to_be_erased=1)

        elif option is self.TrainingOption.EnableTTS and not self._tts_enabled:
            self._tts_enabled = True
            suspend_training_loop(n_lines_to_be_erased=1)

        elif option is self.TrainingOption.ChangePlaybackSpeed:
            self._change_playback_speed()
            suspend_training_loop(n_lines_to_be_erased=2)

        return False

    def _change_playback_speed(self):
        is_valid_playback_speed = lambda playback_speed: 0.1 < playback_speed < 5

        print('Playback speed:\n\t', end='')
        KeyboardController().type(str(self._playback_speed))
        cursor.show()

        _recurse = partial(recurse_on_invalid_input, func=self._change_playback_speed, message='Invalid input', n_deletion_lines=3)

        try:
            altered_playback_speed = float(input())
            cursor.hide()
            if not is_valid_playback_speed(altered_playback_speed):
                return _recurse()
            self._playback_speed = altered_playback_speed
            self._backend.mongodb_client.insert_playback_speed(self._playback_speed)
        except ValueError:
            return _recurse()

    def _modify_latest_vocable_insertion(self, latest_appended_vocable_line: str) -> Tuple[Optional[str], int]:
        """ Returns:
                altered vocable_entry: str, None in case of invalid alteration
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
