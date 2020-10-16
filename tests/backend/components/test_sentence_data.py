import pytest

from lingularity.backend.trainers.base import SentenceData


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
