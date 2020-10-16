import random

import pytest

from lingularity.backend.trainers.base import ForenameConvertor


random.seed(69)


italian_forename_converter = ForenameConvertor("Italian", train_english=False)


@pytest.mark.parametrize('sentence_pair,expected_sentence_pair', [
    (
            ["Unfortunately, Toms handy was stuck in Marys flytrap.", "Purtroppo, Toms Handy è rimasto bloccato nella trappola per mosche di Marie."],
            ['Unfortunately, Francescos handy was stuck in Auroras flytrap.', 'Purtroppo, Francescos Handy è rimasto bloccato nella trappola per mosche di Aurora.']
    ),
    (
            ["Tomorrow, Tom will cut the olive tree.", "Domani Tomás taglierà l'ulivo."],
            ['Tomorrow, Francesco will cut the olive tree.', "Domani Francesco taglierà l'ulivo."]
    ),
    (
            ["Tom told Mary that John wanted to ask Alice for a razor.", "Tom disse a Mary che John voleva chiedere ad Alice un rasoio."],
            ['Edoardo told Emma that Andrea wanted to ask Anna for a razor.', 'Edoardo disse a Emma che Andrea voleva chiedere ad Anna un rasoio.']
    ),
    (
            ["Tom's purpose in college is to get a degree.", "Lo scopo di Tom all'università è laurearsi."],
            ["Gabriele's purpose in college is to get a degree.", "Lo scopo di Gabriele all'università è laurearsi."]
    )
])
def test_forenames_conversion_italian(sentence_pair, expected_sentence_pair):
    for converted, expected in zip(italian_forename_converter(sentence_pair), expected_sentence_pair):
        assert converted == expected
