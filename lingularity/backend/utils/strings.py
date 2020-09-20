from typing import List
import re


def get_meaningful_tokens(sentence: str) -> List[str]:
    """ splitting at relevant delimiters, stripping off semantically irrelevant characters """
    return re.split("[' ’-]", strip_unicode(sentence.translate(str.maketrans('', '', '"!#$%&()*+,./:;<=>?@[\]^`{|}~»«'))))


def strip_unicode(token: str) -> str:
    return token.translate(str.maketrans('', '', "\u2009\u202f\xa0\xa2\u200b"))


def lower_case_sentence_beginnings(sentence: str) -> str:
    chars = list(sentence)
    chars[0] = chars[0].lower()
    point_positions = (i for i in range(len(sentence) - 1) if sentence[i: i + 2] == '. ')
    for i in point_positions:
        chars[i + 2] = chars[i + 2].lower()
    return ''.join(chars)


def get_article_stripped_token(token: str) -> str:
    parts = token.replace("'", ' ').split(' ')
    if len(parts) == 2 and len(parts[0]) < len(parts[1]):
        return parts[1]
    return token


def split_string_at_uppercase(string: str) -> List[str]:
    return re.findall('[A-Z][a-z]*', string)
