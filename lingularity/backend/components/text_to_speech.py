from typing import Optional, List
import os
import time
import vlc
from mutagen.mp3 import MP3

from lingularity.backend.database import MongoDBClient
from lingularity.backend.ops.google.text_to_speech import google_tts
from lingularity.backend.utils.time import get_timestamp


class TextToSpeech:
    _AUDIO_FILE_PATH = f'{os.getcwd()}/.tts_audio_files'

    def __init__(self, language: str, mongodb_client: MongoDBClient):
        self._language: str = language
        self._mongodb_client: MongoDBClient = mongodb_client

        self.language_variety_choices: Optional[List[str]] = google_tts.get_variety_choices(language)
        self._language_variety: Optional[str] = self._query_language_variety()

        if self.available:
            self._playback_speed: float = 1.0 if self._language_variety is None else self._query_playback_speed(self._language_variety) or 1.0
            self._enabled: bool = self._query_enablement() or True

        self._audio_file_path: Optional[str] = None

    @property
    def available(self) -> bool:
        return any([self.language_variety_choices, self._language_variety])

    def __bool__(self) -> bool:
        return self.available and self.enabled

    # -----------------
    # Language Variety
    # -----------------
    def _query_language_variety(self) -> Optional[str]:
        """ Requires _language_variety_2_identifier to be set """

        if self.language_variety_choices is None:
            return self._language

        return self._mongodb_client.query_language_variety_identifier()

    @property
    def language_variety(self) -> Optional[str]:
        return self._language_variety

    @language_variety.setter
    def language_variety(self, variety: str):
        """
            Enters change into database

            Args:
                variety: element of language_variety_choices, e.g. 'Spanish (Spain)'  """

        if variety != self._language_variety:
            if self._language_variety is not None:
                self._mongodb_client.set_language_variety_usage(self._language_variety, False)

            self._language_variety = variety
            self._mongodb_client.set_language_variety_usage(self._language_variety, True)

            del self.audio_file

    # -----------------
    # Enablement
    # -----------------
    def _query_enablement(self) -> bool:
        return self._mongodb_client.query_tts_enablement()

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
    # Playback Speed
    # -----------------
    def _query_playback_speed(self, language_variety: str) -> Optional[float]:
        return self._mongodb_client.query_playback_speed(language_variety)

    @property
    def playback_speed(self) -> Optional[float]:
        return self._playback_speed

    @playback_speed.setter
    def playback_speed(self, value: float):
        assert self._language_variety is not None

        self._playback_speed = value
        self._mongodb_client.insert_playback_speed(self._language_variety, self._playback_speed)

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
        os.remove(self._audio_file_path)
        self._audio_file_path = None

    def download_audio(self, text: str):
        assert self._language_variety is not None

        audio_file_path = f'{self._AUDIO_FILE_PATH}/{get_timestamp()}.mp3'
        google_tts.get_audio(text, self._language_variety, save_path=audio_file_path)

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
