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
            otherwise accent stripped string"

        Special characters have no impact of the working of this function whatsoever and are returned
            as are

        >>>strip_accents('perché')
        perche
        >>>strip_accents("c'est-à-dire")
        c'est-a-dire
        >>>strip_accents('impact')
        impact
        >>>strip_accents('走吧')
        走吧"""

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
    """ Returns:
            None in case of article identification inability

        >>>get_article_stripped_noun('il pomeriggio')
        'il pomeriggio'
        >>>get_article_stripped_noun("l'amour")
        amour
        >>>get_article_stripped_noun("amour")
        None
        >>>get_article_stripped_noun("c'est-à-dire")
        None
        >>>get_article_stripped_noun('nel guai')
        guai """

    if contains_article(noun_candidate):
        return split_multiple(noun_candidate, delimiters=list(APOSTROPHES) + [' '])[1]
    return None


def split_at_uppercase(string: str) -> List[str]:
    return re.findall('[A-Z][a-z]*', string)


def split_multiple(string: str, delimiters: List[str]) -> List[str]:
    return replace_multiple(string, delimiters[:-1], delimiters[-1]).split(delimiters[-1])


def get_meaningful_tokens(text: str, apostrophe_splitting=False) -> Set[str]:
    """ Working Principle:
            - strip special characters, unicode remnants
            - break text into distinct tokens
            - remove tokens containing digit(s)

        >>>get_meaningful_tokens("Parce que il n'avait rien à foutre avec ces 3 saloppes, disait dieu.")
        [Parce, que, il, n'avait, rien, à, foutre, avec, ces, saloppes, disait, dieu] """

    special_character_stripped = strip_special_characters(text, include_apostrophe=False, include_dash=False)
    unicode_stripped = _strip_unicode(special_character_stripped)

    split_characters = ' -'
    if apostrophe_splitting:
        split_characters += APOSTROPHES

    tokens = re.split(f"[{split_characters}]", unicode_stripped)
    return set(filter(is_digit_free, tokens))


def common_start(strings: Iterable[str]) -> str:
    """ Returns:
            empty string in case of strings not possessing common start

        >>>common_start(['spaventare', 'spaventoso', 'spazio'])
        spa
        >>>common_start(['avventura', 'avventurarsi'])
        avventura
        >>>common_start(['nascondersi', 'incolpare'])
        '' """

    buffer = ''
    for strings_i in zip(*strings):
        if len(set(strings_i)) == 1:
            buffer += strings_i[0]
        else:
            break
    return buffer


def longest_continuous_partial_overlap(strings: Iterable[str], min_length=1) -> Optional[str]:
    """ Returns:
            longest retrievable substring of length >= min_length present in at least
            two strings values, None if any of the aforementioned conditions not having
            been met

    >>> longest_continuous_partial_overlap(['メアリーが', 'トムは', 'トムはメアリーを', 'メアリー', 'トムはマリ', 'いた', 'メアリーは'])
    メアリー
    >>> longest_continuous_partial_overlap(['amatur', 'masochist', 'erlaucht', 'manko'])
    ma
    >>> longest_continuous_partial_overlap(['mast', 'merk', 'wucht'], min_length=2)
    None """

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


def is_of_latin_script(string: str, remove_non_alphabetic_characters=True) -> bool:
    """ Args:
            string: regarding which to be determined whether of latin script 
            remove_non_alphabetic_characters: triggers removal of special characters as well as white-spaces
                if set to True, solely for prevention of redundant stripping if already having taken place, since
                REMOVAL INTEGRAL FOR PROPER FUNCTION WORKING

        Returns:
            True if at least 80% of alphabetic characters amongst string pertaining to latin script,
            False otherwise """

    MIN_LATIN_CHARACTER_PERCENTAGE = 80

    if remove_non_alphabetic_characters:
        string = strip_special_characters(string, include_apostrophe=True, include_dash=True).replace(' ', '')

    return len(_to_ascii(string)) / len(string) > (MIN_LATIN_CHARACTER_PERCENTAGE / 100)


def contains_article(noun_candidate: str) -> bool:
    """ Returns:
            True if exactly two distinct tokens present in noun_candidate if split by whitespace
            as well as apostrophes and the first token, that is the article candidate shorter than
            the second, that is the noun candidate """

    return len((tokens := split_multiple(noun_candidate, delimiters=list(APOSTROPHES) + [' ']))) == 2 and len(tokens[0]) < len(tokens[1])


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
            sorted with respect to their lengths

        >>>list(continuous_substrings('path'))
        [pa, at, th, pat, ath, path] """

    if lengths is None:
        lengths = range(min_length, len(string) + 1)
    else:
        lengths = filter(lambda val: val >= min_length, lengths)

    return map(''.join, chain.from_iterable(map(lambda length: windowed(string, length), lengths)))


def _substrings_from_start(string: str) -> Iterator[str]:
    """
    >>> list(_substrings_from_start('path'))
    [p, pa, pat, path] """

    for i in range(1, len(string) + 1):
        yield string[:i]
