from typing import List, Optional
import re


APOSTROPHES = "'’"


def _replace_multiple_characters(text: str, characters: str, replacement: str) -> str:
    for char in characters:
        text = text.replace(char, replacement)
    return text


def strip_multiple_characters(text: str, characters: str) -> str:
    return _replace_multiple_characters(text, characters, replacement='')


def _strip_unicode(token: str) -> str:
    return strip_multiple_characters(token, characters="\u2009\u202f\xa0\xa2\u200b")


def get_meaningful_tokens(text: str, apostrophe_splitting=False) -> List[str]:
    """ Working Principle:
            - strip special characters, unicode remnants
            - break text into distinct tokens
            - remove tokens containing digit(s) """

    special_character_stripped = strip_multiple_characters(text, characters='"!#$%&()*+,./:;<=>?@[\]^`{|}~»«')
    unicode_stripped = _strip_unicode(special_character_stripped)

    split_characters = ' -'
    if apostrophe_splitting:
        split_characters += APOSTROPHES

    tokens = re.split(f"[{split_characters}]", unicode_stripped)
    return list(filter(is_digit_free, tokens))


def get_article_stripped_noun(noun_candidate: str) -> Optional[str]:
    parts = _replace_multiple_characters(noun_candidate, APOSTROPHES, replacement=' ').split(' ')
    if len(parts) == 2 and len(parts[0]) < len(parts[1]):
        return parts[1]
    return None


def split_at_uppercase(string: str) -> List[str]:
    return re.findall('[A-Z][a-z]*', string)


def is_non_latin(char: str) -> bool:
    return ord(char) > 255


def is_digit_free(string: str) -> bool:
    return not any(char.isdigit() for char in string)


def find_common_start(*string: str) -> str:
    _common_start = ''
    for strings_i in zip(*string):
        if len(set(strings_i)) == 1:
            _common_start += strings_i[0]
        else:
            break
    return _common_start

