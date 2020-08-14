""" google libraries demanding language arguments to be passed in corresponding language,
    as well as in the bulk of cases 2-letter comprising abbreviation,
        e.g. spanish -> es
             german -> de
             french -> fr """

from typing import Optional

import gtts

from .translation import language_available as language_available_for_translation, translate


_english_2_corresponding_foreign_language_abbreviation = {v: k for k, v in gtts.lang.tts_langs().items()}


def get_language_abbreviation(english_language: str) -> Optional[str]:
    """ Args:
            english_language: english, written out translation of language in question """

    return _english_2_corresponding_foreign_language_abbreviation.get(english_language)
