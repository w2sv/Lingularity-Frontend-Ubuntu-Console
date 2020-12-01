from typing import Optional
import time

from termcolor import colored

from backend.utils import strings
from backend.trainers.sentence_translation import SentenceTranslationTrainerBackend as Backend, TextToSpeech

from frontend.utils import view, query, output as op
from frontend.trainers.base import TrainerFrontend, SequencePlotData
from frontend.trainers.base.options import TrainingOptions, base_options
from frontend.trainers.sentence_translation import modes, options


_SENTENCE_INDENTATION = op.column_percentual_indentation(0.15)


class SentenceTranslationTrainerFrontend(TrainerFrontend):
    def __init__(self):
        self._tts = TextToSpeech.get_instance()

        super().__init__(backend_type=Backend)
        self._backend: Backend

        self._redo_print = op.RedoPrint()

    def __call__(self) -> SequencePlotData:
        self._set_terminal_title()

        self._set_tts_language_variety_if_applicable()

        self._set_training_mode()
        self._backend.set_item_iterator()

        self._display_training_screen_header_section()
        self._run_training_loop()

        self._backend.enter_session_statistics_into_database(self._n_trained_items)

        return self._training_item_sequence_plot_data()

    def _get_training_options(self) -> TrainingOptions:
        option_classes = [base_options.AddVocable, base_options.RectifyLatestAddedVocableEntry, base_options.Exit]

        if self._tts.available:
            option_classes += [options.EnableTTS, options.DisableTTS, options.ChangePlaybackSpeed]

        if bool(self._tts.language_variety_choices):
            option_classes += [options.ChangeTTSLanguageVariety]

        return TrainingOptions(option_classes=option_classes, frontend_instance=self)  # type: ignore

    @property
    def _training_designation(self) -> str:
        return 'Sentence Translation'

    # -----------------
    # Property Selection
    # -----------------

    # -----------------
    # .Mode
    # -----------------
    def _set_training_mode(self):
        """ Invokes training mode selection method, forwards backend_type of selected mode to backend_type """

        mode_selection = self._select_training_mode()
        self._backend.sentence_data_filter = modes.__getitem__(mode_selection).sentence_data_filter

    @view.creator(header='TRAINING MODES')
    def _select_training_mode(self) -> str:

        # display eligible modes
        indentation = op.block_centering_indentation(modes.explanations)
        for keyword, explanation in zip(modes.keywords, modes.explanations):
            print(f'{indentation}{colored(f"{keyword}:", color="red")}')
            print(f'{indentation}\t{explanation}\n')
        print(view.VERTICAL_OFFSET)

        return query.relentlessly(f'{query.INDENTATION}Enter desired mode: ', options=modes.keywords)

    # -----------------
    # .TTS Language Variety
    # -----------------
    def _set_tts_language_variety_if_applicable(self):
        """ Invokes variety selection method, forwards selected variety to tts """

        if all([self._tts.available, not self._tts.language_variety, self._tts.language_variety_choices]):
            self._tts.language_variety = self._select_tts_language_variety()

    @view.creator(title='TTS Language Variety Selection', banner_args=('language-varieties/larry-3d', 'blue'), vertical_offsets=2)
    def _select_tts_language_variety(self) -> str:
        """ Returns:
                selected language variety: element of language_variety_choices """

        assert self._tts.language_variety_choices is not None

        # discard overlapping variety parts
        common_start_length = len(strings.common_start(self._tts.language_variety_choices))
        processed_varieties = [strings.strip_multiple(dialect[common_start_length:], strings=list('()')) for dialect in self._tts.language_variety_choices]

        # display eligible varieties
        indentation = op.block_centering_indentation(processed_varieties)
        for variety in processed_varieties:
            print(indentation, variety)
        op.empty_row(times=2)

        # query variety
        dialect_selection = query.relentlessly(
            prompt=f'{op.column_percentual_indentation(percentage=0.37)}Enter desired variety: ',
            options=processed_varieties)
        return self._tts.language_variety_choices[processed_varieties.index(dialect_selection)]

    # -----------------
    # Training
    # -----------------
    @view.creator()
    def _display_training_screen_header_section(self):
        self._display_session_information()
        self._training_options.display_instructions(insertion_args=((3, 'TEXT-TO-SPEECH OPTIONS', True),))

        if len(self._training_options) == 3:
            print(view.VERTICAL_OFFSET)
            self._output_lets_go()
            print(view.VERTICAL_OFFSET)
        else:
            self._output_lets_go()

    def _display_session_information(self):
        """ Displays magnitude of underlying sentence data,
            country conversion forenames originating from if applicable """

        op.centered(f"Document comprises {self._backend.n_training_items:,d} sentences.\n")

        # display picked country corresponding to replacement forenames
        if self._backend.forename_converter is not None:
            if demonym := self._backend.forename_converter.demonym:
                op.centered(f'Employing {demonym} forenames.')
            else:
                op.centered(f'Employing forenames stemming from {self._backend.forename_converter.country}.')
        op.empty_row()

    @op.cursor_hider
    def _run_training_loop(self):
        translation = self._process_procured_sentence_pair()

        while translation is not None:
            if self._tts.employ() and self._tts.audio_file is None:
                self._tts.download_audio_file(translation)

            # get response, run selected option if applicable
            response = query.relentlessly('$', options=self._training_options.keywords)

            if len(response):

                # ----OPTION SELECTED----
                if len(response):
                    self._training_options[response].__call__()

                    if self._training_options.exit_training:
                        return

            else:

                # ----ENTER-STROKE----

                # erase pending... + entered option identifier
                op.erase_lines(2)

                # output translation_field
                self._redo_print(f'{_SENTENCE_INDENTATION}{translation}')
                self._redo_print(f'{_SENTENCE_INDENTATION}{colored("─────────────────", "red")}')

                # play tts audio if available, otherwise suspend program
                # for some time to incentivise gleaning over translation_field
                if self._tts.employ():
                    self._tts.play_audio()
                else:
                    time.sleep(len(translation) * 0.05)

                self._n_trained_items += 1

                if self._n_trained_items >= 5:
                    self._redo_print.redo_partially(n_deletion_rows=3)

                translation = self._process_procured_sentence_pair()

        print('\nSentence data file depleted')

    def _process_procured_sentence_pair(self) -> Optional[str]:
        """ Returns:
                translation_field of procured sentence pair, None in case of depleted item iterator """

        if (sentence_pair := self._backend.get_training_item()) is None:
            return None

        # try to convert forenames, output reference language sentence
        if self._backend.forename_converter is not None:
            sentence_pair = self._backend.forename_converter(sentence_pair)

        reference_sentence, translation = sentence_pair

        self._redo_print(f'{_SENTENCE_INDENTATION}{reference_sentence}')
        self._pending_output()

        return translation

    @staticmethod
    def _pending_output():
        print(colored(f"{_SENTENCE_INDENTATION}pending... ", "cyan", attrs=['dark']))

    # -----------------
    # Post Training
    # -----------------
    @property
    def _item_name(self) -> str:
        return 'sentence'

    @property
    def _pluralized_item_name(self) -> str:
        return 'sentences'
