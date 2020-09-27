from googletrans import LANGUAGES, Translator

from . import GoogleOp


class GoogleTranslation(GoogleOp):
    def __init__(self):
        super().__init__(language_2_identifier={v.title(): k for k, v in LANGUAGES.items()})

        self._translator = Translator()

    def translate(self, text: str, src: str, dest: str) -> str:
        """ Args:
                text: to be translated
                src: language identifier of source language
                dest: language identifier of destination language """

        return self._translator.translate(text, src=src, dest=dest).text
