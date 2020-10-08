import os
import time
from typing import Optional, Dict, List

import vlc
from mutagen.mp3 import MP3

from lingularity.backend.database import MongoDBClient
from lingularity.backend.ops.google.tts import GoogleTTS
from lingularity.backend.utils.time import get_timestamp


class TTS:
    _AUDIO_FILE_PATH = f'{os.getcwd()}/.tts_audio_files'

    def __init__(self, language: str, mongodb_client: MongoDBClient):
        self._language: str = language
        self._mongodb_client: MongoDBClient = mongodb_client

        self._google_tts: GoogleTTS = GoogleTTS()

        self._language_variety_2_identifier: Optional[Dict[str, str]] = self._google_tts.get_dialect_choices(language)
        self.language_varieties: Optional[List[str]] = None if self._language_variety_2_identifier is None else list(self._language_variety_2_identifier.keys())
        self.language_varieties_available = bool(self.language_varieties)

        self._language_variety_identifier: Optional[str] = self._query_language_variety_identifier()

        self.available: bool = any([self._language_variety_2_identifier, self._language_variety_identifier])

    @property
    def language_variety_identifier_set(self) -> bool:
        return self._language_variety_identifier is not None

    def query_enablement(self):
        if not self.available:
            return False
        if (flag := self._mongodb_client.query_tts_enablement()) is None:
            return True
        return flag

    def _query_language_variety_identifier(self) -> Optional[str]:
        """ Requires _language_variety_2_identifier to be set """

        if self._language_variety_2_identifier is None:
            return self._google_tts._get_identifier(self._language)

        return self._mongodb_client.query_language_variety_identifier()

    def change_language_variety(self, variety: str):
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

    def query_playback_speed(self) -> Optional[float]:
        if not self.available:
            return None
        else:
            assert self._language_variety_identifier is not None
            if (preset_playback_speed := self._mongodb_client.query_playback_speed(self._language_variety_identifier)) is not None:
                return preset_playback_speed
            else:
                return 1.0

    def enter_playback_speed_change_into_database(self, playback_speed: float):
        assert self._language_variety_identifier is not None

        self._mongodb_client.insert_playback_speed(self._language_variety_identifier, playback_speed)

    def download_audio(self, text: str) -> str:
        assert self._language_variety_identifier is not None

        audio_file_path = f'{self._AUDIO_FILE_PATH}/{get_timestamp()}.mp3'
        self._google_tts.get_tts_audio(text, self._language_variety_identifier, save_path=audio_file_path)
        return audio_file_path

    @staticmethod
    def play_audio_file(audio_file_path: str, playback_rate=1.0, suspend_program_for_duration=False):
        player = vlc.MediaPlayer(audio_file_path)
        player.set_rate(playback_rate)
        player.play()

        if suspend_program_for_duration:
            duration = MP3(audio_file_path).info.length / playback_rate - 0.2
            start_time = time.time()
            while time.time() - start_time < duration:
                # TODO: let function break on enter stroke by employing threading
                pass

    def clear_audio_file_dir(self):
        for audio_file in os.listdir(self._AUDIO_FILE_PATH):
            os.remove(f'{self._AUDIO_FILE_PATH}/{audio_file}')