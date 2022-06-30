from __future__ import annotations

import time

from backend.src.trainers.sentence_translation import SentenceTranslationTrainerBackend
from backend.src.utils.strings.extraction import longest_common_prefix
from backend.src.utils.strings.transformation import strip_multiple
from cursor import cursor
from pynput.keyboard import Controller as Keyboard
from termcolor import colored

from frontend.src.trainers.sentence_translation.modes import MODE_2_EXPLANATION, sentence_filter, SentenceFilterMode
from frontend.src.trainers.sequence_plot_data import SequencePlotData
from frontend.src.trainers.trainer_frontend import TrainerFrontend
from frontend.src.utils import output, output as op, query, view
from frontend.src.utils.output.percentual_indenting import IndentedPrint
from frontend.src.utils.query import PROMPT_INDENTATION
from frontend.src.utils.query.cancelling import QUERY_CANCELLED
from frontend.src.utils.query.repetition import prompt_relentlessly


_SENTENCE_INDENTATION = op.column_percentual_indentation(0.15)


class SentenceTranslationTrainerFrontend(TrainerFrontend[SentenceTranslationTrainerBackend]):
    def __init__(self):
        super().__init__(
            backend_type=SentenceTranslationTrainerBackend,
            item_name='sentence',
            item_name_plural='sentences',
            training_designation='Sentence Translation',
            option_keyword_2_instruction_and_function={
                'enable': ('Enable text-to-speech', self._enable_tts),
                'disable': ('Disable text-to-speech', self._disable_tts),
                'speed': ('Change text-to-speech playback speed', self._change_playback_speed),
                'accent': ('Change text-to-speech accent', self._change_accent)
            }
        )

        self._current_translation = str()
        self._redo_print = op.RedoPrint()

    def __call__(self) -> SequencePlotData:
        self._set_terminal_title()

        self._set_tts_language_variety_if_applicable()

        self._set_training_mode()
        self._backend.set_item_iterator()

        self._display_training_screen_header_section()
        self._training_loop()

        self._backend.enter_session_statistics_into_database(self._n_trained_items)

        return self._training_item_sequence_plot_data()

    # -----------------
    # Property Selection
    # -----------------

    # -----------------
    # .Mode
    # -----------------
    def _set_training_mode(self):
        """ Invokes training mode selection method, forwards backend_type of selected mode to backend_type """

        mode_selection = self._select_training_mode()
        self._backend.sentence_data_filter = sentence_filter(mode_selection)

    @view.creator(header='TRAINING MODES')
    def _select_training_mode(self) -> SentenceFilterMode:

        # display eligible modes
        _print = IndentedPrint(indentation=op.block_centering_indentation(MODE_2_EXPLANATION.values()))
        for mode, explanation in MODE_2_EXPLANATION.items():
            _print(colored(f'{mode.display_name}:', color='red'))
            _print(f'\t{explanation}\n')

        print(view.VERTICAL_OFFSET)

        keyword = prompt_relentlessly(
            f'{PROMPT_INDENTATION}Enter desired mode: ',
            options=[mode.name for mode in MODE_2_EXPLANATION]
        )
        return SentenceFilterMode[keyword]

    # -----------------
    # .TTS Language Variety
    # -----------------
    def _set_tts_language_variety_if_applicable(self):
        """ Invokes variety selection method, forwards selected variety to tts """

        if self._backend.tts_available and len(self._backend.tts.language_variety_choices) and self._backend.tts.language_variety is None:
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
        dialect_selection = prompt_relentlessly(
            prompt=f'{op.column_percentual_indentation(percentage=0.37)}Enter desired variety: ',
            options=processed_varieties)
        return self._backend.tts.language_variety_choices[processed_varieties.index(dialect_selection)]

    # -----------------
    # Training
    # -----------------
    @view.creator()
    def _display_training_screen_header_section(self):
        self._display_session_information()
        self._options.display_instructions(
            row_index_2_insertion_string={2: 'TEXT-TO-SPEECH OPTIONS'}
        )

        if len(self._options) == 3:
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
    def _training_loop(self):
        if translation := self._process_procured_sentence_pair():
            self._current_translation = translation

            if self._backend.tts_available and not self._backend.tts.audio_available:
                self._backend.tts.download_audio(translation)

            # get response, run selected option if applicable
            if self._inquire_option_selection() and self.exit_training:
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
            return self._training_loop()

        print('\nSentence data depleted')

    def _process_procured_sentence_pair(self) -> str | None:
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

    def _enable_tts(self):
        self._backend.tts.enabled = True
        output.erase_lines(1)

    def _disable_tts(self):
        self._backend.tts.enabled = False
        output.erase_lines(1)

    def _change_playback_speed(self):
        def display_prompt():
            print(f'Playback speed:\n{query.PROMPT_INDENTATION}', end='')
            Keyboard().type(str(self._backend.tts.playback_speed))
            cursor.show()

        altered_playback_speed = prompt_relentlessly(
            prompt='',
            prompt_display_function=display_prompt,
            applicability_verifier=self._backend.tts.is_valid_playback_speed,
            error_indication_message='PLAYBACK SPEED HAS TO LIE BETWEEN 0.5 AND 2',
            cancelable=True,
            n_deletion_rows=3,
            sleep_duration=1.5
        )
        cursor.hide()

        if altered_playback_speed == QUERY_CANCELLED:
            return

        self._backend.tts.playback_speed = float(altered_playback_speed)

        output.erase_lines(3)

    def _change_accent(self):
        selected_variety = self._select_tts_language_variety()
        self._backend.tts.language_variety = selected_variety
        if self._backend.tts.audio_available:
            self._backend.tts.download_audio(self._current_translation)

        # redo previous output output
        self._display_training_screen_header_section()
        self._redo_print.redo()
        self._pending_output()