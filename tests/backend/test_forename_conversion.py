from lingularity.backend.trainers import TrainerBackend
from lingularity.backend.database import MongoDBClient

import pytest


class MockTrainer(TrainerBackend):
    def __init__(self):
        super().__init__('Italian', train_english=False, mongodb_client=MongoDBClient('Janek'), vocable_expansion_mode=False)


trainer_stub = MockTrainer()


@pytest.mark.parametrize('sentence_template,insert_names', [
    ("Unfortunately, {}s handy was stuck in {}s flytrap, so, yeah...", ['Tom', 'Mary']),
    ("Unfortunately, {}s handy was stuck.", ['Mary']),
    ("Unfortunately, {} is fancying {} quite a bit.", ['Tom', 'Mary'])
])
def test_forenames_conversion(sentence_template, insert_names):
    sentence = sentence_template.format(*insert_names)

    sentence, picked_names = trainer_stub._convert_forenames(sentence, None)
    assert sentence == sentence_template.format(*filter(lambda name: name is not None, picked_names))
