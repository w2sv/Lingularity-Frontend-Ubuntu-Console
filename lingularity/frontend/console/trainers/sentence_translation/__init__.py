from typing import Optional, Tuple
from itertools import groupby
import cursor
import time

from lingularity.backend.database import MongoDBClient
from lingularity.backend.trainers.sentence_translation import SentenceTranslationTrainerBackend as Backend
from lingularity.backend.components import TextToSpeech
from lingularity.backend.resources import strings as string_resources
from lingularity.backend.utils.strings import common_start, strip_multiple

from . import options
from . import modes
from lingularity.frontend.console.trainers.base import TrainerConsoleFrontend, TrainingOptions
from lingularity.frontend.console.utils.view import view_creator
from lingularity.frontend.console.utils.input_resolution import (
    resolve_input,
    recurse_on_unresolvable_input,
    indissolubility_output
)
from lingularity.frontend.console.utils.terminal import (
    erase_lines,
    centered_print,
    centered_output_block_indentation,
    RedoPrint
)


_redo_print = RedoPrint()


class SentenceTranslationTrainerConsoleFrontend(TrainerConsoleFrontend):
    _TRAINING_LOOP_INDENTATION = ' ' * 16
    _SELECTION_QUERY_OUTPUT_OFFSET = '\n\t'

    def __init__(self, mongodb_client: MongoDBClient):
        self._tts = TextToSpeech.get_instance()

        super().__init__(Backend, mongodb_client)

    def _get_training_options(self) -> TrainingOptions:
        options.SentenceTranslationOption.set_frontend_instance(self)

        option_classes = [options.AddVocabulary, options.AlterLatestVocableEntry, options.Exit]

        if self._tts.available:
            option_classes += [options.EnableTTS, options.DisableTTS, options.ChangePlaybackSpeed]

        if bool(self._tts.language_variety_choices):
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

        self._display_training_screen_header_section()
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

        assert mongodb_client is not None

        train_english = False

        eligible_languages = Backend.get_eligible_languages(mongodb_client)

        # display eligible languages in starting-letter-grouped manner
        starting_letter_grouped_languages = [', '.join(list(v)) for _, v in groupby(eligible_languages, lambda x: x[0])]
        indentation = centered_output_block_indentation(starting_letter_grouped_languages)
        for language_group in starting_letter_grouped_languages:
            print(indentation, language_group)

        # query desired language
        if (selection := resolve_input(input(f'{self._SELECTION_QUERY_OUTPUT_OFFSET}Select language: '), eligible_languages)) is None:
            return recurse_on_unresolvable_input(self._select_training_language, n_deletion_lines=-1)

        # query desired reference language if English selected
        elif selection == string_resources.ENGLISH:
            train_english, selection = True, mongodb_client.query_reference_language()
            eligible_languages.remove(string_resources.ENGLISH)

            erase_lines(2)

            while selection is None:
                if (selection := resolve_input(input(f'{self._SELECTION_QUERY_OUTPUT_OFFSET}Select reference language: '), eligible_languages)) is None:
                    indissolubility_output(n_deletion_lines=2)
                else:
                    mongodb_client.set_reference_language(reference_language=selection)

        return selection, train_english

    def _set_training_mode(self):
        """ Invokes training mode selection method, forwards backend of selected mode to backend """

        mode_selection = self._select_training_mode()
        self._backend.training_mode = modes.__getitem__(mode_selection).backend

    @view_creator(header='TRAINING MODES')
    def _select_training_mode(self) -> str:

        # display eligible modes
        indentation = centered_output_block_indentation(modes.explanations)
        for keyword, explanation in zip(modes.keywords, modes.explanations):
            print(f'{indentation}{keyword.title()}:')
            print(f'{indentation}\t{explanation}\n')

        # query desired mode
        if (mode_selection := resolve_input(input(f'{self._SELECTION_QUERY_OUTPUT_OFFSET}Enter desired mode: '), modes.keywords)) is None:
            return recurse_on_unresolvable_input(self._select_training_mode, n_deletion_lines=-1)
        print('')

        return mode_selection

    def _set_tts_language_variety_if_applicable(self):
        """ Invokes variety selection method, forwards selected variety to tts """

        if all([self._tts.available, not self._tts.language_variety, self._tts.language_variety_choices]):
            self._tts.language_variety = self._select_tts_language_variety()

    @view_creator(header='SELECT TEXT-TO-SPEECH LANGUAGE VARIETY')
    def _select_tts_language_variety(self) -> str:
        """ Returns:
                selected language variety: element of language_variety_choices """

        assert self._tts.language_variety_choices is not None

        # display eligible varieties
        common_start_length = len(common_start(self._tts.language_variety_choices) or '')
        processed_varieties = [strip_multiple(dialect[common_start_length:], strings=list('()')) for dialect in self._tts.language_variety_choices]
        indentation = centered_output_block_indentation(processed_varieties)
        for variety in processed_varieties:
            print(indentation, variety)
        print('')

        # query variety
        if (dialect_selection := resolve_input(input(indentation[:-5]), options=processed_varieties)) is None:
            return recurse_on_unresolvable_input(self._select_tts_language_variety, 1)

        return self._tts.language_variety_choices[processed_varieties.index(dialect_selection)]

    # -----------------
    # Pre training
    # -----------------
    @view_creator(header=None)
    def _display_training_screen_header_section(self):
        self._display_session_information()
        self._display_instructions()
        self._output_lets_go()

    def _display_session_information(self):
        centered_print(f"Document comprises {self._backend.n_training_items:,d} sentences.\n")

        # display picked country corresponding to replacement forenames
        if self._backend.forenames_convertible:
            if demonym := self._backend.forename_converter.demonym:
                centered_print(f'Employing {demonym} forenames.')
            else:
                centered_print(f'Employing forenames stemming from {self._backend.forename_converter.country}.')
        print('')

    def _display_instructions(self):
        instructions = ["      Enter:"] + self._training_options.instructions
        indentation = centered_output_block_indentation(instructions)
        for i, line in enumerate(instructions):
            # display intermediate tts option header if applicable
            if i == 4:
                centered_print('\nText-to-Speech Options\n'.upper())

            print(indentation, line)

        print('\n' * 2, end='')

    # -----------------
    # Training
    # -----------------
    def _run_training(self):
        translation = self._process_procured_sentence_pair()

        while translation is not None:
            if self._tts.employ() and self._tts.audio_file is None:
                self._tts.download_audio_file(translation)

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

                    # output translation_field
                    _redo_print(f'{self._TRAINING_LOOP_INDENTATION}{translation}')
                    _redo_print(f'{self._TRAINING_LOOP_INDENTATION}_______________')

                    # play tts audio if available, otherwise suspend program
                    # for some time to incentivise gleaning over translation_field
                    if self._tts.employ():
                        self._tts.play_audio()
                    else:
                        time.sleep(len(translation) * 0.05)

                    self._n_trained_items += 1

                    if self._n_trained_items >= 5:
                        _redo_print.redo_partially(n_deletion_lines=3)

                    translation = self._process_procured_sentence_pair()

            else:
                indissolubility_output(n_deletion_lines=2)

        print('\nSentence data file depleted')

    def _process_procured_sentence_pair(self) -> Optional[str]:
        """ Returns:
                translation_field of procured sentence pair, None in case of depleted item iterator """

        if (sentence_pair := self._backend.get_training_item()) is None:
            return None

        # try to convert forenames, output reference language sentence
        if self._backend.forenames_convertible:
            reference_sentence, translation = self._backend.forename_converter(sentence_pair)  # type: ignore
        else:
            reference_sentence, translation = sentence_pair

        _redo_print(f'{self._TRAINING_LOOP_INDENTATION}{reference_sentence}')
        self._pending_output()

        return translation

    def _pending_output(self):
        print(f"{self._TRAINING_LOOP_INDENTATION}pending... ")

    # -----------------
    # Post Training
    # -----------------
    @property
    def _item_name(self) -> str:
        return 'sentence'

    @property
    def _pluralized_item_name(self) -> str:
        return 'sentences'
