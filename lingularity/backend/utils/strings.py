from typing import List, Optional, Set, Iterable
import re
import unicodedata


APOSTROPHES = "'’"


# ---------------
# Modification
# ---------------
def replace_multiple(text: str, strings: List[str], replacement: str) -> str:
    for string in strings:
        text = text.replace(string, replacement)
    return text


def strip_multiple(text: str, strings: List[str]) -> str:
    return replace_multiple(text, strings, replacement='')


def _strip_unicode(token: str) -> str:
    return strip_multiple(token, strings=list("\u2009\u202f\xa0\xa2\u200b"))


def _to_ascii(string: str) -> str:
    """ Reference: https://stackoverflow.com/questions/517923/what-is-the-best
                   -way-to-remove-accents-normalize-in-a-python-unicode-string

        Returns:
             ascii-transformed string, that is a string whose non-ascii characters have been
             transformed to their respective ascii-equivalent,
                e.g. Odlično -> Odlicno,
                     vilkår -> vilkar,
                     Söýgi -> Soygi
             whilst such not possessing an equivalent are removed,
                e.g. Hjælp -> Hjlp,
                     Dođi -> Doi,
                     等等我 -> ''

        Special characters have no impact of the working of this function whatsoever and are returned
            as are """

    return unicodedata.normalize('NFKD', string).encode('ASCII', 'ignore').decode()


def strip_accents(string: str) -> str:
    """ Returns:
            original string in case of string not being of latin script,
            otherwise accent stripped string. e.g. remove_accent("c'est-à-dire") -> "c'est-a-dire"

        Special characters have no impact of the working of this function whatsoever and are returned
            as are """

    if is_of_latin_script(string):
        return _to_ascii(string)
    return string


def strip_special_characters(string: str, include_apostrophe=False, include_dash=False) -> str:
    special_characters = '"!#$%&()*+,./:;<=>?@[\]^_`{|}~»«。¡¿'

    if include_apostrophe:
        special_characters += APOSTROPHES
    if include_dash:
        special_characters += '-'

    return strip_multiple(string, strings=list(special_characters))


# ---------------
# Extraction
# ---------------
def get_article_stripped_noun(noun_candidate: str) -> Optional[str]:
    parts = replace_multiple(noun_candidate, list(APOSTROPHES), replacement=' ').split(' ')
    if len(parts) == 2 and len(parts[0]) < len(parts[1]):
        return parts[1]
    return None


def split_at_uppercase(string: str) -> List[str]:
    return re.findall('[A-Z][a-z]*', string)


def get_meaningful_tokens(text: str, apostrophe_splitting=False) -> Set[str]:
    """ Working Principle:
            - strip special characters, unicode remnants
            - break text into distinct tokens
            - remove tokens containing digit(s) """

    special_character_stripped = strip_special_characters(text, include_apostrophe=False, include_dash=False)
    unicode_stripped = _strip_unicode(special_character_stripped)

    split_characters = ' -'
    if apostrophe_splitting:
        split_characters += APOSTROPHES

    tokens = re.split(f"[{split_characters}]", unicode_stripped)
    return set(filter(is_digit_free, tokens))


def find_common_start(*string: str) -> str:
    common_start = ''
    for strings_i in zip(*string):
        if len(set(strings_i)) == 1:
            common_start += strings_i[0]
        else:
            break
    return common_start


# ---------------
# Classification
# ---------------
def is_digit_free(string: str) -> bool:
    return not any(char.isdigit() for char in string)


def is_of_latin_script(string: str, trim=True) -> bool:
    MIN_LATIN_CHARACTER_PERCENTAGE = 80

    if trim:
        string = strip_special_characters(string, include_apostrophe=True, include_dash=True).strip(' ')

    return len(_to_ascii(string)) / len(string) > (MIN_LATIN_CHARACTER_PERCENTAGE / 100)
