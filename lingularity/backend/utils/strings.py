from typing import List, Optional, Set, Iterator, Iterable
from itertools import chain
import unicodedata
import re

from lingularity.backend.utils.iterables import windowed, longest_value


APOSTROPHES = "'’́́́́́́́́́́́́"


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
    special_characters = '"„“!#$%&()*+,./:;<=>?@[\]^_`{|}~»«。¡¿'

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


def split_multiple(string: str, delimiters: List[str]) -> List[str]:
    return replace_multiple(string, delimiters[:-1], delimiters[-1]).split(delimiters[-1])


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


def common_start(strings: Iterable[str]) -> Optional[str]:
    buffer = ''
    for strings_i in zip(*strings):
        if len(set(strings_i)) == 1:
            buffer += strings_i[0]
        else:
            break
    return [None, buffer][bool(len(buffer))]


def longest_continuous_partial_overlap(strings: Iterable[str], min_length=2) -> Optional[str]:
    buffer = ''
    substrings_list = list(map(lambda string: set(_substrings_from_start(string)), strings))
    for i, substrings in enumerate(substrings_list):
        for comparison in substrings_list[i + 1:]:
            buffer = longest_value([buffer, longest_value(substrings & comparison | {''})])
    return [None, buffer][len(buffer) > min_length]


# ---------------
# Classification
# ---------------
def is_digit_free(string: str) -> bool:
    return not any(char.isdigit() for char in string)


def is_of_latin_script(string: str, trim=True) -> bool:
    MIN_LATIN_CHARACTER_PERCENTAGE = 80

    if trim:
        string = strip_special_characters(string, include_apostrophe=True, include_dash=True).replace(' ', '')

    return len(_to_ascii(string)) / len(string) > (MIN_LATIN_CHARACTER_PERCENTAGE / 100)


# ---------------
# Substrings
# ---------------
def continuous_substrings(string: str, lengths: Optional[Iterable[int]] = None, min_length=2) -> Iterator[str]:
    """
        Args:
            string: string to extract substrings from
            lengths: Iterable of desired substring lengths,
                may contain lengths > len(string) which will be automatically ignored

        Returns:
            Iterator of entirety of continuous substrings of min length = 2 comprised by string
            sorted with respect to their lengths, e.g.:
                continuous_substrings('path') -> Iterator[
                    'pa', 'at', 'th',
                    'pat', 'ath',
                    'path'
                ] """

    if lengths is None:
        lengths = range(min_length, len(string) + 1)
    else:
        lengths = filter(lambda val: val >= min_length, lengths)

    return map(''.join, chain.from_iterable(map(lambda length: windowed(string, length), lengths)))


def _substrings_from_start(string: str) -> Iterator[str]:
    for i in range(1, len(string) + 1):
        yield string[:i]


if __name__ == '__main__':
    print(longest_continuous_partial_overlap(['メアリーが', 'トムは', 'トムはメアリーを', 'メアリー', 'トムはマリ', 'いた', 'メアリーは']))
    print(split_multiple("asdf'sadf safdcxvyXasdf", list("'X ")))