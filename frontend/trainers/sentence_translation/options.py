__all__ = ['ChangeTTSLanguageVariety', 'EnableTTS',
           'DisableTTS', 'ChangePlaybackSpeed']

from functools import partial

import cursor
from pynput.keyboard import Controller as Keyboard

from frontend.utils import query, output
from frontend.trainers.base.options import TrainingOption


class EnableTTS(TrainingOption):
    def __init__(self):
        self.keyword, self.explanation = 'enable', 'enable speech output'

    def __call__(self):
        self._tts.enabled = True
        output.erase_lines(1)


class DisableTTS(TrainingOption):
    def __init__(self):
        self.keyword, self.explanation = 'disable', 'disable speech output'

    def __call__(self):
        self._tts.enabled = False
        output.erase_lines(1)


class ChangePlaybackSpeed(TrainingOption):
    def __init__(self):
        self.keyword, self.explanation = 'speed', 'change playback speed'

    def __call__(self):
        self._change_playback_speed()
        output.erase_lines(3)

    def _change_playback_speed(self):
        print(f'Playback speed:\n{query.HORIZONTAL_OFFSET}', end='')
        Keyboard().type(str(self._tts.playback_speed))
        cursor.show()

        _recurse = partial(query.repeat, function=self._change_playback_speed, message='INVALID INPUT', n_deletion_lines=3)

        try:
            altered_playback_speed = float(input())
            cursor.hide()

            if not self._tts.is_valid_playback_speed(altered_playback_speed):
                return _recurse()

            self._tts.playback_speed = altered_playback_speed

        except ValueError:
            return _recurse()


class ChangeTTSLanguageVariety(TrainingOption):
    def __init__(self):
        self.keyword, self.explanation = 'variety', 'change text-to-speech language variety'

    def __call__(self):
        selected_variety = self._select_tts_language_variety()
        self._tts.language_variety = selected_variety

        # redo previous output output
        self._display_training_screen_header_section()
        self._redo_print.redo()
        self._pending_output()
