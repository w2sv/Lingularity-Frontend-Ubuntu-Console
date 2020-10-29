import os

import gtts

from lingularity.backend.utils import data
from lingularity.backend.ops.google import GoogleOp


class GoogleTextToSpeech(GoogleOp):
    _IDENTIFIER_DATA_FILE_PATH = f'{os.path.dirname(__file__)}/identifiers'

    def __init__(self):
        super().__init__(language_2_identifier=data.load_json(self._IDENTIFIER_DATA_FILE_PATH))

    def get_audio(self, text: str, language: str, save_path: str):
        gtts.gTTS(text, lang=self._get_identifier(language)).save(save_path)

    @staticmethod
    def mine_identifier_data():
        data.write_json({v: k for k, v in gtts.tts.tts_langs().items()}, file_path=GoogleTextToSpeech._IDENTIFIER_DATA_FILE_PATH)


google_tts = GoogleTextToSpeech()
