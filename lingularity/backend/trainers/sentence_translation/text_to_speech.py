from typing import Optional, List
import os
import time

import vlc

from lingularity.utils import either
from lingularity.backend.utils.state_sharing import MonoStatePossessor
from lingularity.backend.database import MongoDBClient
from lingularity.backend.ops.google.text_to_speech import google_tts
from lingularity.backend.utils.time import get_timestamp


class TextToSpeech(MonoStatePossessor):
    _AUDIO_FILE_PATH = f'{os.getcwd()}/.tts_audio_files'

    def __init__(self, language: str):
        super().__init__()

        self._mongodb_client: MongoDBClient = MongoDBClient.get_instance()

        self.language_variety_choices: Optional[List[str]] = google_tts.get_variety_choices(language)
        self._language_variety: Optional[str] = self._get_language_variety(language)

        if self.available:
            self._playback_speed: float = self._get_playback_speed(self._language_variety)
            self._enabled: bool = self._get_enablement()

        self._audio_file_path: Optional[str] = None

    @property
    def available(self) -> bool:
        return any([self.language_variety_choices, self._language_variety])

    def employ(self) -> bool:
        return self.available and self.enabled

    # -----------------
    # Language Variety
    # -----------------
    def _get_language_variety(self, language: str) -> Optional[str]:
        """ Returns:
                language if no variety choices available,
                otherwise:
                    variety with enablement being set to True in database if language has already been used,
                    None if not """

        if self.language_variety_choices is None:
            return [None, language][google_tts.available_for(language)]

        return self._mongodb_client.query_language_variety()

    @property
    def language_variety(self) -> Optional[str]:
        return self._language_variety

    @language_variety.setter
    def language_variety(self, variety: str):
        """ Args:
                variety: element of language_variety_choices, e.g. 'Spanish (Spain)'

            Enters change into database, deletes audio file of old variety """

        # avoid unnecessary database calls
        if variety != self._language_variety:

            # set usage of current variety to False in database if already assigned
            if self._language_variety is not None:
                self._mongodb_client.set_language_variety_usage(self._language_variety, False)

            self._language_variety = variety

            # set usage of new variety to True in database
            self._mongodb_client.set_language_variety_usage(self._language_variety, True)

            # delete possibly downloaded audio file pertaining to old variety in order to
            # trigger download of file pertaining to new one in subsequent training loop iteration
            if self.audio_file is not None:
                del self.audio_file

    # -----------------
    # Enablement
    # -----------------
    def _get_enablement(self) -> bool:
        """ Returns:
                previously stored enablement corresponding to language if existent,
                otherwise default of True """

        return either(self._mongodb_client.query_tts_enablement(), True)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, enable: bool):
        """ Triggers deletion of audio file if switching from enabled to disabled,
            enters change into database """

        # avoid unnecessary database calls
        if enable != self._enabled:
            self._enabled = enable

            # delete audio file if tts getting disabled
            if not self._enabled:
                del self.audio_file

            # enter change into database
            self._mongodb_client.set_tts_enablement(self._enabled)

    # -----------------
    # Playback Speed
    # -----------------
    def _get_playback_speed(self, language_variety: Optional[str]) -> float:
        """" Returns:
                previously stored playback speed corresponding to language_variety if existent
                    otherwise default of 1.0 """

        if language_variety is not None and (stored_playback_speed := self._mongodb_client.query_playback_speed(language_variety)) is not None:
            return stored_playback_speed
        return 1.0

    @property
    def playback_speed(self) -> Optional[float]:
        return self._playback_speed

    @playback_speed.setter
    def playback_speed(self, value: float):
        assert self._language_variety is not None

        # avoid unnecessary database calls
        if value != self._playback_speed:
            self._playback_speed = value
            self._mongodb_client.set_playback_speed(self._language_variety, self._playback_speed)

    @staticmethod
    def is_valid_playback_speed(playback_speed: float) -> bool:
        return 0.1 < playback_speed < 3

    # -----------------
    # Usage
    # -----------------
    @property
    def audio_file(self) -> Optional[str]:
        return self._audio_file_path

    @audio_file.setter
    def audio_file(self, file_path: str):
        self._audio_file_path = file_path

    @audio_file.deleter
    def audio_file(self):
        """ Deletes audio file, sets audio_file_path to None """

        if self._audio_file_path is not None:
            os.remove(self._audio_file_path)

        self._audio_file_path = None

    def download_audio_file(self, text: str):
        assert self._language_variety is not None

        audio_file_path = f'{self._AUDIO_FILE_PATH}/{get_timestamp()}.mp3'
        google_tts.get_audio(text, self._language_variety, save_path=audio_file_path)

        self._audio_file_path = audio_file_path

    @staticmethod
    def _audio_length(audio_file_path: str, bits_per_second=500) -> float:
        return os.path.getsize(audio_file_path) / 8 / bits_per_second

    def play_audio(self):
        """ Suspends program for playback duration, deletes audio file subsequently """

        player = vlc.MediaPlayer(self.audio_file)
        player.set_rate(self._playback_speed)
        player.play()

        start_time = time.time()

        assert self.audio_file is not None

        duration = self._audio_length(self.audio_file) / self._playback_speed - 0.2
        while time.time() - start_time < duration:
            # TODO: let function break on enter stroke by employing threading
            pass

        del self.audio_file

    def __del__(self):
        """ Triggers deletion of all audio files on object destruction """

        for audio_file in os.listdir(TextToSpeech._AUDIO_FILE_PATH):
            os.remove(f'{TextToSpeech._AUDIO_FILE_PATH}/{audio_file}')
