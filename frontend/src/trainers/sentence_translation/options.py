__all__ = ['ChangeTTSLanguageVariety', 'EnableTTS',
           'DisableTTS', 'ChangePlaybackSpeed']

import cursor
from pynput.keyboard import Controller as Keyboard

from frontend.src.utils import query, output
from frontend.src.trainers.base.options import TrainingOption


class EnableTTS(TrainingOption):
    def __init__(self):
        self.keyword, self.explanation = 'enable', 'enable speech output'

    def __call__(self):
        self._backend.tts.enabled = True
        output.erase_lines(1)


class DisableTTS(TrainingOption):
    def __init__(self):
        self.keyword, self.explanation = 'disable', 'disable speech output'

    def __call__(self):
        self._backend.tts.enabled = False
        output.erase_lines(1)


class ChangePlaybackSpeed(TrainingOption):
    def __init__(self):
        self.keyword, self.explanation = 'speed', 'change playback speed'

    def __call__(self):
        self._change_playback_speed()
        output.erase_lines(3)

    def _change_playback_speed(self):
        def display_prompt():
            print(f'Playback speed:\n{query.INDENTATION}', end='')
            Keyboard().type(str(self._tts.playback_speed))
            cursor.show()

        altered_playback_speed = query.relentlessly(prompt='',
                                                    prompt_display_function=display_prompt,
                                                    applicability_verifier=self._tts.is_valid_playback_speed,
                                                    error_indication_message='PLAYBACK SPEED HAS TO LIE BETWEEN 0.5 AND 2',
                                                    cancelable=True,
                                                    n_deletion_rows=3,
                                                    sleep_duration=1.5)
        cursor.hide()

        if altered_playback_speed == query.CANCELLED:
            return

        self._backend.tts.playback_speed = float(altered_playback_speed)

class ChangeTTSLanguageVariety(TrainingOption):
    def __init__(self):
        self.keyword, self.explanation = 'variety', 'change text-to-speech language variety'

    def __call__(self):
        selected_variety = self._select_tts_language_variety()
        self._backend.tts.language_variety = selected_variety

        # redo previous output output
        self._display_training_screen_header_section()
        self._redo_print.redo()
        self._pending_output()
