import pytest
import os
import random

from lingularity.backend import SENTENCE_DATA_PATH
from lingularity.backend.utils import strings
from lingularity.backend.trainers.base import SentenceData


def _random_language() -> str:
    return random.choice(os.listdir(SENTENCE_DATA_PATH)).split('.')[0]


@pytest.mark.parametrize('language', [
    (_random_language()),
    (_random_language()),
    (_random_language())
])
def test_reading_in(language):
    sentence_data = SentenceData(language)

    for column in [sentence_data.english_sentences, sentence_data.foreign_language_sentences]:
        assert all(map(lambda character: not strings.contains_escape_sequence(character), column.comprising_characters))


# ----------------
# Column
# ----------------
@pytest.mark.parametrize('language,expected', [
    ('French', True),
    ('Spanish', True),
    ('Croatian', True),
    ('Japanese', False),
    ('Chinese', False),
    ('Russian', False),
    ('Arabic', False),
    ('Serbian', False)
])
def test_employs_latin_alphabet(language, expected):
    assert SentenceData(language).foreign_language_sentences.uses_latin_script == expected


@pytest.mark.parametrize('language,tokens,expected', [
    ('Chinese', ['Tom', 'Mary'], False),
    ('German', ["c'est-à-dire"], False),
    ('French', ['Tom', 'Mary'], True),
    ('Italian', ['faccia', 'prigione', 'abbraccerà'], True),
    ('Korean', ['고마워', '잡아'], True)
])
def test_comprises_tokens(language, tokens, expected):
    assert SentenceData(language).foreign_language_sentences.comprises_tokens(query_tokens=tokens) == expected
