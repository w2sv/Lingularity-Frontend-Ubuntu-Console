import time
from typing import Optional

from backend.src.trainers.sentence_translation import SentenceTranslationTrainerBackend
from backend.src.utils.strings.extraction import longest_common_prefix
from backend.src.utils.strings.transformation import strip_multiple
from termcolor import colored

from frontend.src.trainers.base import SequencePlotData, TrainerFrontend
from frontend.src.trainers.base.options import base_options, TrainingOptions
from frontend.src.trainers.sentence_translation import modes, options
from frontend.src.utils import output as op, query, view
from frontend.src.utils.query.repetition import query_relentlessly


_SENTENCE_INDENTATION = op.column_percentual_indentation(0.15)


class SentenceTranslationTrainerFrontend(TrainerFrontend[SentenceTranslationTrainerBackend]):
    def __init__(self):
        super().__init__(
            backend_type=SentenceTranslationTrainerBackend,
            item_name='sentence',
            item_name_plural='sentences',
            training_designation='Sentence Translation'
        )

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

        if self._backend.tts_available:
            option_classes += [options.EnableTTS, options.DisableTTS, options.ChangePlaybackSpeed]

            if bool(self._backend.tts.language_variety_choices):
                option_classes += [options.ChangeTTSLanguageVariety]

        return TrainingOptions(option_classes=option_classes, frontend_instance=self)

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

        return query_relentlessly(f'{query.INDENTATION}Enter desired mode: ', options=modes.keywords)

    # -----------------
    # .TTS Language Variety
    # -----------------
    def _set_tts_language_variety_if_applicable(self):
        """ Invokes variety selection method, forwards selected variety to tts """

        if all([self._backend.tts_available, not self._backend.tts.language_variety, self._backend.tts.language_variety_choices]):
            self._backend.tts.language_variety = self._select_tts_language_variety()

    @view.creator(title='TTS Language Variety Selection', banner_args=('language-varieties/larry-3d', 'blue'), vertical_offsets=2)
    def _select_tts_language_variety(self) -> str:
        """ Returns:
                selected language variety: element of language_variety_choices """

        assert self._backend.tts.language_variety_choices is not None

        # discard overlapping variety parts
        common_start_length = len(longest_common_prefix(self._backend.tts.language_variety_choices))
        processed_varieties = [strip_multiple(dialect[common_start_length:], strings=list('()')) for dialect in self._backend.tts.language_variety_choices]

        # display eligible varieties
        indentation = op.block_centering_indentation(processed_varieties)
        for variety in processed_varieties:
            print(indentation, variety)
        op.empty_row(times=2)

        # query variety
        dialect_selection = query_relentlessly(
            prompt=f'{op.column_percentual_indentation(percentage=0.37)}Enter desired variety: ',
            options=processed_varieties)
        return self._backend.tts.language_variety_choices[processed_varieties.index(dialect_selection)]

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
            if self._backend.tts_available and not self._backend.tts.audio_available:
                self._backend.tts.download_audio(translation)

            # get response, run selected option if applicable
            response = query_relentlessly('$', options=self._training_options.keywords)

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
                # for some time to encourage gleaning over translation_field
                if self._backend.tts_available and self._backend.tts.enabled and self._backend.tts.audio_available:
                    self._backend.tts.play_audio()
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
