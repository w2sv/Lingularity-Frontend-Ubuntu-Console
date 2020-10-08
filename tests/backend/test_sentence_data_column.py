import pytest

from lingularity.backend.trainers.base import SentenceData


@pytest.mark.parametrize('language,expected', [
    ('Arabic', False),
    ('French', True),
    ('Spanish', True),
    ('Croatian', True),
    ('Japanese', False),
    ('Chinese', False)
])
def test_employs_latin_alphabet(language, expected):
    assert SentenceData(language).foreign_language_sentences.uses_latin_script == expected


@pytest.mark.parametrize('language,tokens,expected', [
    ('Chinese', ['Tom', 'Mary'], False),
    ('French', ['Tom', 'Mary'], True),
    ('Italian', ['faccia', 'priso'], True),
    ('German', ["c'est-à-dire"], False)
])
def test_comprises_tokens(language, tokens, expected):
    assert SentenceData(language).foreign_language_sentences.comprises_tokens(query_tokens=tokens) == expected
