import gtts

from . import GoogleOp


class GoogleTTS(GoogleOp):
    def __init__(self):
        super().__init__({v: k for k, v in gtts.lang.tts_langs().items()})

    @staticmethod
    def get_audio(text: str, language_identifier: str, save_path: str):
        gtts.gTTS(text, lang=language_identifier).save(save_path)


google_tts = GoogleTTS()
