from typing import List
import re


def get_meaningful_tokens(sentence: str) -> List[str]:
    """ splitting at relevant delimiters, stripping off semantically irrelevant characters """
    sentence = sentence.translate(str.maketrans('', '', '"!#$%&()*+,./:;<=>?@[\]^`{|}~»«'))
    return re.split("[' ’\u2009\u202f\xa0\xa2-]", sentence)


def strip_unicode(token: str) -> str:
    return token.translate(str.maketrans('', '', "\u2009\u202f\xa0\xa2"))


def lower_case_sentence_beginnings(sentence: str) -> str:
    chars = list(sentence)
    chars[0] = chars[0].lower()
    point_positions = [i for i in range(len(sentence) - 1) if sentence[i: i + 2] == '. ']
    if point_positions:
        for i in point_positions:
            chars[i + 2] = chars[i + 2].lower()
    return ''.join(chars)
