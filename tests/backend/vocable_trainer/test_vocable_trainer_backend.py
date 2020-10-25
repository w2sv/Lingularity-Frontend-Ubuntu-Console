from lingularity.backend.trainers.vocable_trainer import VocableTrainerBackend
from tests.utils import get_vocable_entries


def test_find_synonyms():
    EXPECTED = {'next to': ['di fianco', 'accanto a'], 'face': ['la faccia', 'il viso']}

    assert VocableTrainerBackend._find_synonyms(get_vocable_entries()) == EXPECTED
