from lingularity.backend.trainers.base import ForenameConvertor

import pytest


forename_converter = ForenameConvertor("Italian", train_english=False)


@pytest.mark.parametrize('sentence_pair_template,insert_names', [
    (["Unfortunately, {}s handy was stuck in {}s flytrap.", "Purtroppo, {}s Handy è rimasto bloccato nella trappola per mosche di {}."], ['Tom', 'Mary']),
    (["Tomorrow, {} will cut the olive tree.", "Domani {} taglierà l'ulivo."], ['Tom']),
    (["{} told {} that {} wanted to ask {} for a razor.", "{} disse a {} che {} voleva chiedere ad {} un rasoio."], ['Tom', 'Mary', 'John', 'Alice']),
])
def test_forenames_conversion(sentence_pair_template, insert_names):
    sentence_pair = list(map(lambda sentence: sentence.format(*insert_names), sentence_pair_template))
    converted_sentence_pair = forename_converter(sentence_pair)
    assert not any(any(default_forename in sentence for default_forename in insert_names) for sentence in converted_sentence_pair)
