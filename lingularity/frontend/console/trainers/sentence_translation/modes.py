from typing import *
from itertools import starmap

from lingularity.backend.utils.iterables import unzip
from lingularity.backend.utils.strings import split_at_uppercase
from lingularity.backend.trainers.sentence_translation import modes as mode_backends


class TrainingMode:
    def __init__(self, mode_backend: Type[mode_backends.TrainingMode], explanation: str):
        self.keyword: str = ' '.join(map(lambda part: part.lower(), split_at_uppercase(mode_backend.__name__)))
        self.explanation: str = explanation
        self.backend: Type[mode_backends.TrainingMode] = mode_backend


_modes = list(starmap(TrainingMode, (
    (mode_backends.DictionExpansion, 'show me sentences containing rather infrequently used vocabulary'),
    (mode_backends.Simple, 'show me sentences comprising exclusively commonly used vocabulary'),
    (mode_backends.Random, 'just hit me with dem sentences'))))


keywords, explanations = unzip(map(lambda mode: (mode.keyword, mode.explanation), _modes))
_keyword_2_mode = {mode.keyword: mode for mode in _modes}


def __getitem__(item: str) -> TrainingMode:
    return _keyword_2_mode[item]
