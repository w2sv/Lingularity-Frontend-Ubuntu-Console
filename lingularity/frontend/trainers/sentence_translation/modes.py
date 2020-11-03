from types import ModuleType
from itertools import starmap

from lingularity.backend.utils import iterables, strings
from lingularity.backend.trainers.sentence_translation import modes


class TrainingMode:
    def __init__(self, mode_module: ModuleType, explanation: str):
        self.keyword: str = strings.snake_case_to_title(snake_case_string=mode_module.__name__.split('.')[-1])
        self.explanation: str = explanation
        self.sentence_data_filter: modes.SentenceDataFilter = mode_module.filter_sentence_data  # type: ignore


_modes = list(starmap(TrainingMode, (
    (modes.diction_expansion, 'show me sentences containing rather infrequently used vocabulary'),
    (modes.simple, 'show me sentences comprising exclusively commonly used vocabulary'),
    (modes.random, 'just hit me with dem sentences'))))


keywords, explanations = iterables.unzip(map(lambda mode: (mode.keyword, mode.explanation), _modes))
_keyword_2_mode = {mode.keyword: mode for mode in _modes}


def __getitem__(item: str) -> TrainingMode:
    return _keyword_2_mode[item]
