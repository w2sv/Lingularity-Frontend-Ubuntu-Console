import socket

from googletrans import LANGUAGES, Translator

from lingularity.backend.ops.google import GoogleOp


socket.setdefaulttimeout(15 * 60)


class GoogleTranslator(GoogleOp):
    _translator: Translator

    def __init__(self):
        super().__init__(language_2_identifier={v.title(): k for k, v in LANGUAGES.items()})

        if not hasattr(GoogleTranslator, '_translator'):
            GoogleTranslator._translator = Translator()

    def translate(self, text: str, dest: str, src: str) -> str:
        """ Args:
                text: to be translated
                src: titular source language
                dest: titular destination language """

        return self._translator.translate(text, *map(self._get_identifier, [dest, src])).text


google_translator = GoogleTranslator()
