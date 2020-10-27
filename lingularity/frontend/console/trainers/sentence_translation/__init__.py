from typing import Optional
import time

from lingularity.backend.trainers.sentence_translation import SentenceTranslationTrainerBackend as Backend, TextToSpeech
from lingularity.backend.utils.strings import common_start, strip_multiple

from . import options
from . import modes
from lingularity.frontend.console.trainers.base import TrainerConsoleFrontend, TrainingOptions
from lingularity.frontend.console.reentrypoint import ReentryPoint
from lingularity.frontend.console.utils import view, input_resolution
from lingularity.frontend.console.utils.output import (
    erase_lines,
    centered_print,
    centered_block_indentation,
    RedoPrint,
    SELECTION_QUERY_OUTPUT_OFFSET,
    cursor_hider
)


_redo_print = RedoPrint()


class SentenceTranslationTrainerConsoleFrontend(TrainerConsoleFrontend):
    _TRAINING_LOOP_INDENTATION = ' ' * 16

    def __init__(self):
        self._tts = TextToSpeech.get_instance()

        super().__init__(backend=Backend)

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
    def __call__(self) -> ReentryPoint:
        self._set_tts_language_variety_if_applicable()

        self._set_training_mode()
        self._backend.set_item_iterator()

        self._display_training_screen_header_section()
        self._run_training_loop()

        self._backend.enter_session_statistics_into_database(self._n_trained_items)
        self._plot_training_chronic()

        return ReentryPoint.TrainingSelection

    # -----------------
    # Training Property Selection
    # -----------------
    def _set_training_mode(self):
        """ Invokes training mode selection method, forwards backend of selected mode to backend """

        mode_selection = self._select_training_mode()
        self._backend.training_mode = modes.__getitem__(mode_selection).backend

    @view.view_creator(header='TRAINING MODES')
    def _select_training_mode(self) -> str:

        # display eligible modes
        indentation = centered_block_indentation(modes.explanations)
        for keyword, explanation in zip(modes.keywords, modes.explanations):
            print(f'{indentation}{keyword.title()}:')
            print(f'{indentation}\t{explanation}\n')

        return input_resolution.query_relentlessly(f'{SELECTION_QUERY_OUTPUT_OFFSET}Enter desired mode: ', options=modes.keywords)

    def _set_tts_language_variety_if_applicable(self):
        """ Invokes variety selection method, forwards selected variety to tts """

        if all([self._tts.available, not self._tts.language_variety, self._tts.language_variety_choices]):
            self._tts.language_variety = self._select_tts_language_variety()

    @view.view_creator(header='SELECT TEXT-TO-SPEECH LANGUAGE VARIETY')
    def _select_tts_language_variety(self) -> str:
        """ Returns:
                selected language variety: element of language_variety_choices """

        assert self._tts.language_variety_choices is not None

        # display eligible varieties
        common_start_length = len(common_start(self._tts.language_variety_choices))
        processed_varieties = [strip_multiple(dialect[common_start_length:], strings=list('()')) for dialect in self._tts.language_variety_choices]
        indentation = centered_block_indentation(processed_varieties)
        for variety in processed_varieties:
            print(indentation, variety)
        print('')

        # query variety
        dialect_selection = input_resolution.query_relentlessly(query_message=indentation[:-5], options=processed_varieties)
        return self._tts.language_variety_choices[processed_varieties.index(dialect_selection)]

    # -----------------
    # Pre training
    # -----------------
    @view.view_creator(header=None)
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
        head, indentation = self._get_instruction_head_and_indentation()

        print(f'{indentation}{head}')
        for i, instruction_row in enumerate(self._training_options.instructions):
            # display intermediate tts option header if applicable
            if i == 4:
                centered_print('\nTEXT-TO-SPEECH OPTIONS\n')

            print(f'{indentation}  {instruction_row}')

        print('\n' * 2, end='')

    # -----------------
    # Training
    # -----------------
    @cursor_hider
    def _run_training_loop(self):
        translation = self._process_procured_sentence_pair()

        while translation is not None:
            if self._tts.employ() and self._tts.audio_file is None:
                self._tts.download_audio_file(translation)

            # get response, execute selected option if applicable
            response = input_resolution.query_relentlessly('$', options=self._training_options.keywords + [''])

            if len(response):

                # ----OPTION SELECTED----
                if len(response):
                    self._training_options[response].execute()

                    if type(self._training_options[response]) is options.Exit:
                        return

            else:

                # ----ENTER-STROKE----

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
