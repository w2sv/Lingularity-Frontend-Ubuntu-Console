from __future__ import annotations

import time

from backend.src.trainers.sentence_translation import SentenceTranslationTrainerBackend
from cursor import cursor
from pynput.keyboard import Controller as Keyboard
import stringcase
from termcolor import colored

from frontend.src.plot_parameters import PlotParameters
from frontend.src.trainer_frontends.sentence_translation.modes import get_sentence_filter, MODE_2_EXPLANATION, SentenceFilterMode
from frontend.src.trainer_frontends.sentence_translation.screens import mode_selection, tts_accent_selection
from frontend.src.trainer_frontends.trainer_frontend import TrainerFrontend
from frontend.src.utils import output, output as op, prompt, view
from frontend.src.utils.prompt.cancelling import QUERY_CANCELLED
from frontend.src.utils.prompt.repetition import prompt_relentlessly


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

        self._mode: SentenceFilterMode = None  # type: ignore
        self._current_translation = str()
        self._redo_print = op.RedoPrint()

    def __call__(self) -> PlotParameters:
        self._set_terminal_title()

        self._set_tts_accent_if_applicable()

        self._set_training_mode()
        self._backend.set_item_iterator()

        self._display_training_screen_header_section()
        self._training_loop()

        self._upsert_session_statistics()

        return self._training_item_sequence_plot_data()

    # -----------------
    # Property Selection
    # -----------------

    # -----------------
    # .Mode
    # -----------------
    def _set_training_mode(self):
        """ Invokes training mode selection method, forwards backend_type of selected mode to backend_type """

        self._mode = mode_selection.__call__()
        self._backend.sentence_data_filter = get_sentence_filter(self._mode)

    # -----------------
    # .TTS Language Variety
    # -----------------
    def _set_tts_accent_if_applicable(self):
        """ Invokes variety selection method, forwards selected variety to tts """

        if self._backend.tts_available and len(self._backend.tts.accent_choices):
            self._backend.tts.accent = tts_accent_selection.__call__(tts_accent_choices=self._backend.tts.accent_choices)

    # -----------------
    # Training
    # -----------------
    @view.creator()
    def _display_training_screen_header_section(self):
        self._display_session_information()
        self._options.display_instructions(
            row_index_2_insertion_string={2: 'TEXT-TO-SPEECH OPTIONS'}
        )
        self._output_lets_go()

    def _display_session_information(self):
        """ Displays magnitude of underlying sentence data,
            country conversion forenames originating from if applicable """

        op.centered(f'{stringcase.titlecase(self._mode.name)} mode comprises {self._backend.n_training_items:,d} sentences.')

        if self._backend.forename_converter:
            op.empty_row()

            if demonym := self._backend.forename_converter.demonym:
                op.centered(f'Employing {demonym} forenames.')
            else:
                op.centered(f'Employing forenames from {self._backend.forename_converter.country}.')
        if self._backend.tts.accent:
            op.empty_row()

            op.centered(f'TTS Accent Region: {self._backend.tts.accent}')

        op.empty_row()

    @op.cursor_hider
    def _training_loop(self):
        if translation := self._process_procured_sentence_pair():
            self._current_translation = translation

            if self._backend.tts_available and not self._backend.tts.audio_available:
                self._backend.tts.download_audio(translation)

            # get response, run selected option if applicable
            if self._inquire_option_selection() and self._quit_training:
                return

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
            print(f'Playback speed:\n{prompt.PROMPT_INDENTATION}', end='')
            Keyboard().type(str(self._backend.tts.playback_speed))
            cursor.show()

        altered_playback_speed = prompt_relentlessly(
            prompt=str(),
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
        self._set_tts_accent_if_applicable()

        if self._backend.tts.audio_available:
            self._backend.tts.download_audio(self._current_translation)

        # redo previous output
        self._display_training_screen_header_section()
        self._redo_print.redo()
        self._pending_output()