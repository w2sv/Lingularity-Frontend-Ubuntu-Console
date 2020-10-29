__all__ = ['SentenceTranslationOption', 'AddVocabulary', 'AlterLatestVocableEntry', 'ChangeTTSLanguageVariety',
           'EnableTTS', 'DisableTTS', 'ChangePlaybackSpeed', 'Exit']

from abc import ABC
from time import sleep
from functools import partial

import cursor
from pynput.keyboard import Controller as Keyboard

from lingularity.frontend.console.utils import input_resolution, output
from lingularity.frontend.console.trainers.base.options import TrainingOption


class SentenceTranslationOption(TrainingOption, ABC):
    _FRONTEND_INSTANCE = None

    @staticmethod
    def set_frontend_instance(instance):
        SentenceTranslationOption._FRONTEND_INSTANCE = instance


class AddVocabulary(SentenceTranslationOption):
    def __init__(self):
        self.keyword, self.explanation = 'vocabulary', 'add a vocable'

    def __call__(self):
        n_printed_lines = self._add_vocable()
        output.erase_lines(n_printed_lines + 1)


class AlterLatestVocableEntry(SentenceTranslationOption):
    def __init__(self):
        self.keyword, self.explanation = 'alter', 'alter the most recently added vocable entry'

    def __call__(self):
        if self._latest_created_vocable_entry is None:
            output.centered_print("You haven't added any vocabulary during the current session")
            sleep(1.5)
            output.erase_lines(2)
        else:
            n_printed_lines = self._alter_vocable_entry(self._latest_created_vocable_entry)
            output.erase_lines(n_printed_lines)


class Exit(SentenceTranslationOption):
    def __init__(self):
        self.keyword, self.explanation = 'quit', 'return to training selection screen'

    def __call__(self):
        output.erase_lines(1)
        print(f'\nNumber of faced sentences: {self._n_trained_items}')


class EnableTTS(SentenceTranslationOption):
    def __init__(self):
        self.keyword, self.explanation = 'enable', 'enable speech output'

    def __call__(self):
        self._tts.enabled = True
        output.erase_lines(1)


class DisableTTS(SentenceTranslationOption):
    def __init__(self):
        self.keyword, self.explanation = 'disable', 'disable speech output'

    def __call__(self):
        self._tts.enabled = False
        output.erase_lines(1)


class ChangePlaybackSpeed(SentenceTranslationOption):
    def __init__(self):
        self.keyword, self.explanation = 'speed', 'change playback speed'

    def __call__(self):
        self._change_playback_speed()
        output.erase_lines(3)

    def _change_playback_speed(self):
        print(f'Playback speed:{output.SELECTION_QUERY_OUTPUT_OFFSET}', end='')
        Keyboard().type(str(self._tts.playback_speed))
        cursor.show()

        _recurse = partial(input_resolution.repeat, function=self._change_playback_speed, message='Invalid input', n_deletion_lines=3)

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
        self.keyword, self.explanation = 'variety', 'change text-to-speech language variety'

    def __call__(self):
        selected_variety = self._select_tts_language_variety()
        self._tts.language_variety = selected_variety

        # redo previous output output
        self._display_training_screen_header_section()
        self._buffer_print.redo()
        self._pending_output()
