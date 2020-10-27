import gtts

from . import GoogleOp


class GoogleTextToSpeech(GoogleOp):
    def __init__(self):
        super().__init__({v: k for k, v in gtts.tts.tts_langs().items()})

    def get_audio(self, text: str, language: str, save_path: str):
        gtts.gTTS(text, lang=self._get_identifier(language)).save(save_path)


google_tts = GoogleTextToSpeech()
