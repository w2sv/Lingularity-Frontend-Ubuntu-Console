from googletrans import LANGUAGES, Translator


_translator = Translator()


def language_available(language: str) -> bool:
    return language in LANGUAGES


def translate(content: str, src: str, dest: str) -> str:
    """ Args:
            Refer to google.__init__ concerning the required form of src, dest """

    return _translator.translate(content, src=src, dest=dest).text
