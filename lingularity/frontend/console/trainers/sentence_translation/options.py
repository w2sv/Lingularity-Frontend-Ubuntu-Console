__all__ = ['SentenceTranslationOption', 'AddVocabulary', 'AlterLatestVocableEntry', 'ChangeTTSLanguageVariety',
           'EnableTTS', 'DisableTTS', 'ChangePlaybackSpeed', 'Exit']

from abc import ABC
from time import sleep
from functools import partial

import cursor
from pynput.keyboard import Controller as KeyboardController

from lingularity.frontend.console.utils.output import centered_print, erase_lines
from lingularity.frontend.console.utils.input_resolution import recurse_on_invalid_input
from lingularity.frontend.console.trainers.base.options import TrainingOption


class SentenceTranslationOption(TrainingOption, ABC):
    _FRONTEND_INSTANCE = None

    @staticmethod
    def set_frontend_instance(instance):
        SentenceTranslationOption._FRONTEND_INSTANCE = instance

    def __init__(self, keyword: str, explanation: str):
        super().__init__(keyword, explanation)

    def _alter_tts_enablement(self, value: bool):
        self._tts_enabled = value
        self._backend.mongodb_client.set_tts_enablement(value)
        erase_lines(1)


class AddVocabulary(SentenceTranslationOption):
    def __init__(self):
        super().__init__('vocabulary', 'add a vocable')

    def execute(self):
        n_printed_lines = self._get_new_vocable()
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
        self._backend.tts.clear_audio_file_dir()
        erase_lines(1)
        print(f'\nNumber of faced sentences: {self._n_trained_items}')
        cursor.show()


class EnableTTS(SentenceTranslationOption):
    def __init__(self):
        super().__init__('enable', 'enable speech output')

    def execute(self):
        self._alter_tts_enablement(value=True)


class DisableTTS(SentenceTranslationOption):
    def __init__(self):
        super().__init__('disable', 'disable speech output')

    def execute(self):
        self._remove_audio_file()
        self._alter_tts_enablement(value=False)


class ChangePlaybackSpeed(SentenceTranslationOption):
    def __init__(self):
        super().__init__('speed', 'change playback speed')

    def execute(self):
        self._change_playback_speed()
        erase_lines(3)

    def _change_playback_speed(self):
        def is_valid(playback_speed: float) -> bool:
            return 0.1 < playback_speed < 3

        print('Playback speed:\n\t', end='')
        KeyboardController().type(str(self._playback_speed))
        cursor.show()

        _recurse = partial(recurse_on_invalid_input, function=self._change_playback_speed, message='Invalid input', n_deletion_lines=3)

        try:
            altered_playback_speed = float(input())
            cursor.hide()
            if not is_valid(altered_playback_speed):
                return _recurse()
            self._playback_speed = altered_playback_speed
            self._backend.tts.enter_playback_speed_change_into_database(altered_playback_speed)
        except ValueError:
            return _recurse()


class ChangeTTSLanguageVariety(SentenceTranslationOption):
    def __init__(self):
        super().__init__('variety', 'change text-to-speech language variety')

    def execute(self):
        selected_variety = self._select_language_variety()
        self._backend.tts.change_language_variety(selected_variety)
        self._remove_audio_file()

        # redo previous terminal output
        self._display_instructions()
        self._buffer_print._redo()
        self._pending_output()
