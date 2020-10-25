from lingularity.backend.trainers.vocable_trainer.response_evaluation import (
    get_response_evaluation,
    _n_char_deviations,
    ResponseEvaluation
)

import pytest


@pytest.mark.parametrize('response,ground_truth,expected', [
    ('scopare', 'scopare', 0),
    ('scoware', 'scopare', 1),
    ('scoppare', 'scopare', 1),
    ('scoare', 'scopare', 1),
    ('sad', 'scopare', 6),
    ('', 'scopare', 7),
    ('socpare', 'scopare', 2),
    ('scoprare', 'scopare', 1),
    ('scossare', 'scorsare', 1)
])
def test_n_char_deviations(response, ground_truth, expected):
    assert _n_char_deviations(response, ground_truth) == expected


@pytest.mark.parametrize('response,ground_truth,expected', [
    ('', 'il meglio', ResponseEvaluation.NoResponse),
    ('la meglio', 'il meglio', ResponseEvaluation.WrongArticle),
    ('meglio', 'il meglio', ResponseEvaluation.MissingArticle),
    ('scopar', 'scopare', ResponseEvaluation.AlmostCorrect),
    ('sopravalutare', 'sopravvalutare', ResponseEvaluation.AlmostCorrect),
    ('ci si beca', 'ci si becca', ResponseEvaluation.AlmostCorrect),
    ('ce si beca', 'ci si becca', ResponseEvaluation.Wrong),
    ('sopravallutare', 'sopravvalutare', ResponseEvaluation.Wrong),
    ('sopar', 'scopare', ResponseEvaluation.Wrong),
    ('oppare', 'scopare', ResponseEvaluation.Wrong),
    ('scossare', 'scopare', ResponseEvaluation.Wrong),
    ('scopare', 'scopare', ResponseEvaluation.Correct),
    ('ventredi', 'ventredì', ResponseEvaluation.AccentError),
    ('ventrèdì', 'ventredì', ResponseEvaluation.AccentError)
])
def test_get_response_evaluation(response, ground_truth, expected):
    assert get_response_evaluation(response, ground_truth)[1] is expected
