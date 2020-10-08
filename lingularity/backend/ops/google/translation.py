from googletrans import LANGUAGES, Translator

from . import GoogleOp


class GoogleTranslator(GoogleOp):
    def __init__(self):
        super().__init__(language_2_identifier={v.title(): k for k, v in LANGUAGES.items()})

        self._translator = Translator()

    def translate(self, text: str, src: str, dest: str) -> str:
        """ Args:
                text: to be translated
                src: titular source language
                dest: titular destination language """

        return self._translator.translate(text, *map(self._get_identifier, [src, dest])).text


google_translator = GoogleTranslator()
