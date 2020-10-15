from typing import Optional, Tuple
from itertools import groupby
import cursor
import time
import os

from lingularity.backend.database import MongoDBClient
from lingularity.backend.trainers.sentence_translation import SentenceTranslationTrainerBackend as Backend
from lingularity.backend.utils.strings import common_start, strip_multiple
from lingularity.backend.resources import strings as string_resources

from . import options
from . import modes
from lingularity.frontend.console.trainers.base import TrainerConsoleFrontend
from ..base import TrainingOptions
from lingularity.frontend.console.utils.view import view_creator
from lingularity.frontend.console.utils.input_resolution import (
    resolve_input,
    recurse_on_unresolvable_input,
    indissolubility_output
)
from lingularity.frontend.console.utils.output import (
    erase_lines,
    centered_print,
    centered_output_block_indentation,
)


class SentenceTranslationTrainerConsoleFrontend(TrainerConsoleFrontend):
    _TRAINING_LOOP_INDENTATION = ' ' * 16

    def __init__(self, mongodb_client: MongoDBClient):
        super().__init__(Backend, mongodb_client)

        self._tts_enabled: bool = self._backend.tts.query_enablement()
        self._playback_speed: Optional[float] = self._backend.tts.query_playback_speed()
        self._audio_file_path: Optional[str] = None

    def _get_training_options(self) -> TrainingOptions:
        options.SentenceTranslationOption.set_frontend_instance(self)

        option_classes = [options.AddVocabulary, options.AlterLatestVocableEntry, options.Exit]

        if self._backend.tts.available:
            option_classes += [options.EnableTTS, options.DisableTTS, options.ChangePlaybackSpeed]

        if self._backend.tts.language_varieties_available:
            option_classes += [options.ChangeTTSLanguageVariety]

        return TrainingOptions(option_classes)  # type: ignore

    # -----------------
    # Driver
    # -----------------
    def __call__(self) -> bool:
        self._set_tts_language_variety_if_applicable()

        self._set_training_mode()
        self._backend.set_item_iterator()

        cursor.hide()

        self._display_training_screen_header()
        self._run_training()

        self._backend.enter_session_statistics_into_database(self._n_trained_items)
        self._plot_training_chronic()

        return False

    # -----------------
    # Training Property Selection
    # -----------------
    @view_creator(header='ELIGIBLE LANGUAGES')
    def _select_training_language(self, mongodb_client: Optional[MongoDBClient] = None) -> Tuple[str, bool]:
        """ Returns:
                non-english language: str
                train_english: bool """

        train_english = False

        eligible_languages = Backend.get_eligible_languages(mongodb_client)

        # display eligible languages in starting-letter-grouped manner
        starting_letter_grouped_languages = [', '.join(list(v)) for _, v in groupby(eligible_languages, lambda x: x[0])]
        indentation = centered_output_block_indentation(starting_letter_grouped_languages)
        for language_group in starting_letter_grouped_languages:
            print(indentation, language_group)

        # query desired language
        if (selection := resolve_input(input(f'{self.SELECTION_QUERY_OUTPUT_OFFSET}Select language: '), eligible_languages)) is None:
            return recurse_on_unresolvable_input(self._select_training_language, n_deletion_lines=-1)

        # query desired reference language if English selected
        elif selection == string_resources.ENGLISH:
            selection, train_english = None, True
            eligible_languages.remove(string_resources.ENGLISH)

            while selection is None:
                if (selection := resolve_input(input(f'{self.SELECTION_QUERY_OUTPUT_OFFSET}Select reference language: '), eligible_languages)) is None:
                    indissolubility_output(n_deletion_lines=2)

        return selection, train_english

    def _set_tts_language_variety_if_applicable(self):
        """ Invokes variety selection method, forwards selected variety to backend """

        if all([self._backend.tts.available, self._backend.tts.language_varieties, not self._backend.tts.language_variety_identifier_set]):
            variety_selection = self._select_tts_language_variety()
            self._backend.tts.change_language_variety(variety=variety_selection)

    @view_creator(header='SELECT TEXT-TO-SPEECH LANGUAGE VARIETY')
    def _select_tts_language_variety(self) -> str:
        """ Returns:
                selected language variety: element of language_varieties """

        assert self._backend.tts.language_varieties is not None

        # display eligible varieties
        common_start_length = len(common_start(self._backend.tts.language_varieties) or '')
        processed_varieties = [strip_multiple(dialect[common_start_length:], strings=list('()')) for dialect in self._backend.tts.language_varieties]
        indentation = centered_output_block_indentation(processed_varieties)
        for variety in processed_varieties:
            print(indentation, variety)
        print('')

        # query variety
        if (dialect_selection := resolve_input(input(indentation[:-5]), options=processed_varieties)) is None:
            return recurse_on_unresolvable_input(self._select_tts_language_variety, 1)

        return self._backend.tts.language_varieties[processed_varieties.index(dialect_selection)]

    def _set_training_mode(self):
        """ Invokes training mode selection method, forwards backend of selected mode to backend """

        mode_selection = self._select_training_mode()
        self._backend.set_training_mode(modes.__getitem__(mode_selection).backend)

    @view_creator(header='TRAINING MODES')
    def _select_training_mode(self) -> str:
        # display eligible modes
        indentation = centered_output_block_indentation(modes.explanations)
        for keyword, explanation in zip(modes.keywords, modes.explanations):
            print(f'{indentation}{keyword.title()}:')
            print(f'{indentation}\t{explanation}\n')

        # query desired mode
        if (mode_selection := resolve_input(input(f'{self.SELECTION_QUERY_OUTPUT_OFFSET}Enter desired mode: '), modes.keywords)) is None:
            return recurse_on_unresolvable_input(self._select_training_mode, n_deletion_lines=-1)
        print('')

        return mode_selection

    # -----------------
    # Pre training
    # -----------------
    @view_creator(header=None)
    def _display_training_screen_header(self):

        # display number of sentences comprised by filtered sentence data
        centered_print(f"Document comprises {self._backend.n_training_items:,d} sentences.\n")

        # display picked country corresponding to replacement forenames
        if self._backend.forename_converter.forenames_convertible:
            centered_print(f'Employing {self._backend.forename_converter.demonym} forenames.')
        print('')

        # display instructions
        instructions = ["      Enter:"] + self._training_options.instructions
        indentation = centered_output_block_indentation(instructions)
        for i, line in enumerate(instructions):
            print(indentation, line)

            # display intermediate tts option header if applicable
            if i == 3:
                centered_print('\nText-to-Speech Options\n'.upper())

        # display let's go
        print('\n' * 2, end='')
        self._output_lets_go()

    # -----------------
    # Training
    # -----------------
    @property
    def _tts_available_and_enabled(self) -> bool:
        return self._backend.tts.available and self._tts_enabled

    def _run_training(self):
        translation = self._process_procured_sentence_pair()

        while translation is not None:
            # get tts audio file if available
            if self._tts_available_and_enabled and self._audio_file_path is None:
                self._audio_file_path = self._backend.tts.download_audio(text=translation)

            # get response, execute selected option if applicable
            if (response := resolve_input(input('$'), options=self._training_options.keywords + [''])) is not None:

                # ----OPTION SELECTED----
                if len(response):
                    self._training_options[response].execute()

                    if type(self._training_options[response]) is options.Exit:
                        return

                # ----ENTER-STROKE----
                else:
                    # erase pending... + entered option identifier
                    erase_lines(2)

                    # output translation
                    self._buffer_print(f'{self._TRAINING_LOOP_INDENTATION}{translation}')
                    self._buffer_print(f'{self._TRAINING_LOOP_INDENTATION}_______________')

                    # play tts file if available, otherwise suspend program
                    # for some time to incentivise gleaning over translation
                    if self._tts_available_and_enabled:
                        self._backend.tts.play_audio_file(self._audio_file_path, self._playback_speed, suspend_program_for_duration=True)
                        self._remove_audio_file()
                    else:
                        time.sleep(len(translation) * 0.05)

                    self._n_trained_items += 1

                    if self._n_trained_items >= 5:
                        self._buffer_print.redo_partially(n_deletion_lines=3)

                    translation = self._process_procured_sentence_pair()

            else:
                indissolubility_output(n_deletion_lines=2)

        print('\nSentence data file depleted')

    def _process_procured_sentence_pair(self) -> Optional[str]:
        """ Returns:
                translation of procured sentence pair, None in case of depleted item iterator """

        if (sentence_pair := self._backend.get_training_item()) is None:
            return None

        # try to convert forenames, output reference language sentence
        reference_sentence, translation = self._backend.forename_converter(sentence_pair)
        self._buffer_print(f'{self._TRAINING_LOOP_INDENTATION}{reference_sentence}')
        self._pending_output()

        return translation

    def _remove_audio_file(self):
        os.remove(self._audio_file_path)
        self._audio_file_path = None

    def _pending_output(self):
        print(f"{self._TRAINING_LOOP_INDENTATION}pending... ")
