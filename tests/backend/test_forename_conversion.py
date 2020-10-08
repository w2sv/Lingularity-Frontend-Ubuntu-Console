from lingularity.backend.trainers.base import ForenameConvertor

import pytest


forename_converter = ForenameConvertor("Italian")


@pytest.mark.parametrize('sentence_template,insert_names', [
    ("Unfortunately, {}s handy was stuck in {}s flytrap, so, yeah...", ['Tom', 'Mary']),
    ("Unfortunately, {}s handy was stuck.", ['Mary']),
    ("Unfortunately, {} is fancying {} quite a bit.", ['Tom', 'Mary'])
])
def test_forenames_conversion(sentence_template, insert_names):
    sentence = sentence_template.format(*insert_names)

    sentence, picked_names = forename_converter._convert_sentence(sentence, None)
    assert sentence == sentence_template.format(*filter(lambda name: name is not None, picked_names))
