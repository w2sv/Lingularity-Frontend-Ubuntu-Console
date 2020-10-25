__all__ = ['SentenceTranslationOption', 'AddVocabulary', 'AlterLatestVocableEntry', 'ChangeTTSLanguageVariety',
           'EnableTTS', 'DisableTTS', 'ChangePlaybackSpeed', 'Exit']

from abc import ABC
from time import sleep
from functools import partial

import cursor
from pynput.keyboard import Controller as Keyboard

from lingularity.frontend.console.utils.input_resolution import repeat
from lingularity.frontend.console.utils.console import centered_print, erase_lines
from lingularity.frontend.console.trainers.base.options import TrainingOption


class SentenceTranslationOption(TrainingOption, ABC):
    _FRONTEND_INSTANCE = None

    @staticmethod
    def set_frontend_instance(instance):
        SentenceTranslationOption._FRONTEND_INSTANCE = instance

    def __init__(self, keyword: str, explanation: str):
        super().__init__(keyword, explanation)


class AddVocabulary(SentenceTranslationOption):
    def __init__(self):
        super().__init__('vocabulary', 'add a vocable')

    def execute(self):
        n_printed_lines = self._add_vocable()
        erase_lines(n_printed_lines + 1)


class AlterLatestVocableEntry(SentenceTranslationOption):
    def __init__(self):
        super().__init__('alter', 'alter the most recently added vocable entry')

    def execute(self):
        if self._latest_created_vocable_entry is None:
            centered_print("You haven't added any vocabulary during the current session")
            sleep(1.5)
            erase_lines(2)
        else:
            n_printed_lines = self._alter_vocable_entry(self._latest_created_vocable_entry)
            erase_lines(n_printed_lines)


class Exit(SentenceTranslationOption):
    def __init__(self):
        super().__init__('exit', 'terminate program')

    def execute(self):
        erase_lines(1)
        print(f'\nNumber of faced sentences: {self._n_trained_items}')
        cursor.show()


class EnableTTS(SentenceTranslationOption):
    def __init__(self):
        super().__init__('enable', 'enable speech output')

    def execute(self):
        self._tts.enabled = True
        erase_lines(1)


class DisableTTS(SentenceTranslationOption):
    def __init__(self):
        super().__init__('disable', 'disable speech output')

    def execute(self):
        self._tts.enabled = False
        erase_lines(1)


class ChangePlaybackSpeed(SentenceTranslationOption):
    def __init__(self):
        super().__init__('speed', 'change playback speed')

    def execute(self):
        self._change_playback_speed()
        erase_lines(3)

    def _change_playback_speed(self):
        print('Playback speed:\n\t', end='')
        Keyboard().type(str(self._tts.playback_speed))
        cursor.show()

        _recurse = partial(repeat, function=self._change_playback_speed, message='Invalid input', n_deletion_lines=3)

        try:
            altered_playback_speed = float(input())
            cursor.hide()

            if not self._tts.is_valid_playback_speed(altered_playback_speed):
                return _recurse()

            self._tts.playback_speed = altered_playback_speed

        except ValueError:
            return _recurse()


class ChangeTTSLanguageVariety(SentenceTranslationOption):
    def __init__(self):
        super().__init__('variety', 'change text-to-speech language variety')

    def execute(self):
        selected_variety = self._select_tts_language_variety()
        self._tts.language_variety = selected_variety

        # redo previous console output
        self._display_training_screen_header_section()
        self._buffer_print.redo()
        self._pending_output()
