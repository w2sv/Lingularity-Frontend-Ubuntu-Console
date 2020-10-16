import os
import time
from typing import Optional, Dict, List

import vlc
from mutagen.mp3 import MP3

from lingularity.backend.database import MongoDBClient
from lingularity.backend.ops.google.tts import google_tts
from lingularity.backend.utils.time import get_timestamp


class TextToSpeech:
    _AUDIO_FILE_PATH = f'{os.getcwd()}/.tts_audio_files'

    def __init__(self, language: str, mongodb_client: MongoDBClient):
        self._language: str = language
        self._mongodb_client: MongoDBClient = mongodb_client

        self._language_variety_2_identifier: Optional[Dict[str, str]] = google_tts.get_dialect_choices(language)
        self.language_varieties: Optional[List[str]] = None if self._language_variety_2_identifier is None else list(self._language_variety_2_identifier.keys())

        self._language_variety_identifier: Optional[str] = self._query_language_variety_identifier()

        self.available: bool = any([self._language_variety_2_identifier, self._language_variety_identifier])

        self._playback_speed: Optional[float] = self._query_playback_speed()
        self._enabled: bool = self._query_enablement()

        self._audio_file_path: Optional[str] = None

    def __bool__(self) -> bool:
        return self.available and self.enabled

    @property
    def audio_file(self) -> Optional[str]:
        return self._audio_file_path

    @audio_file.setter
    def audio_file(self, file_path: str):
        self._audio_file_path = file_path

    @audio_file.deleter
    def audio_file(self):
        os.remove(self._audio_file_path)
        self._audio_file_path = None

    # -----------------
    # Playback Speed
    # -----------------
    def _query_playback_speed(self) -> Optional[float]:
        if not self.available:
            return None

        assert self._language_variety_identifier is not None

        if (preset_playback_speed := self._mongodb_client.query_playback_speed(self._language_variety_identifier)) is not None:
            return preset_playback_speed
        return 1.0

    @property
    def playback_speed(self) -> Optional[float]:
        return self._playback_speed

    @playback_speed.setter
    def playback_speed(self, value: float):
        self._playback_speed = value
        self._mongodb_client.insert_playback_speed(self._language_variety_identifier, self._playback_speed)

    @staticmethod
    def is_valid_playback_speed(playback_speed: float) -> bool:
        return 0.1 < playback_speed < 3

    # -----------------
    # Enablement
    # -----------------
    def _query_enablement(self) -> bool:
        if not self.available:
            return False
        elif (flag := self._mongodb_client.query_tts_enablement()) is None:
            return True
        return flag

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, enable: bool):
        if enable != self._enabled:

            if not enable:
                del self.audio_file

            self._enabled = enable
            self._mongodb_client.set_tts_enablement(enable)

    # -----------------
    # Language Variety
    # -----------------
    def _query_language_variety_identifier(self) -> Optional[str]:
        """ Requires _language_variety_2_identifier to be set """

        if self._language_variety_2_identifier is None:
            return google_tts._get_identifier(self._language)

        return self._mongodb_client.query_language_variety_identifier()

    @property
    def language_variety(self) -> Optional[str]:
        return self._language_variety_identifier

    @language_variety.setter
    def language_variety(self, variety: str):
        """
            Assumes previous assertion of _language_variety_2_identifier not being None

            Enters change into database

            Args:
                variety: element of language_varieties, e.g. 'Spanish (Spain)'  """

        assert self._language_variety_2_identifier is not None

        if self._language_variety_identifier is not None:
            self._mongodb_client.set_language_variety_usage(self._language_variety_identifier, False)

        self._language_variety_identifier = self._language_variety_2_identifier[variety]
        self._mongodb_client.set_language_variety_usage(self._language_variety_identifier, True)

    # -----------------
    # Usage
    # -----------------
    def download_audio(self, text: str):
        assert self._language_variety_identifier is not None

        audio_file_path = f'{self._AUDIO_FILE_PATH}/{get_timestamp()}.mp3'
        google_tts.get_audio(text, self._language_variety_identifier, save_path=audio_file_path)

        self._audio_file_path = audio_file_path

    def play_audio(self):
        """ Suspends program for the playback duration """

        player = vlc.MediaPlayer(self.audio_file)
        player.set_rate(self._playback_speed)
        player.play()

        start_time, duration = time.time(), MP3(self.audio_file).info.length / self._playback_speed - 0.2
        while time.time() - start_time < duration:
            # TODO: let function break on enter stroke by employing threading
            pass

        del self.audio_file

    def __del__(self):
        for audio_file in os.listdir(TextToSpeech._AUDIO_FILE_PATH):
            os.remove(f'{TextToSpeech._AUDIO_FILE_PATH}/{audio_file}')
