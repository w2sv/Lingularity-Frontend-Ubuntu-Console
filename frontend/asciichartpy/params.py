from __future__ import annotations
from dataclasses import dataclass
from math import floor, ceil

from frontend.asciichartpy.types import _Sequences
from frontend.asciichartpy.config import Config


@dataclass(frozen=True)
class Params:
    ratio: float
    minimum: int
    maximum: int
    n_rows: int
    width: int

    @classmethod
    def compute(cls, sequences: _Sequences, config: Config) -> Params:
        ratio = config.height / [1, config.interval][config.interval > 0]

        minimum = int(floor(config.min * ratio))
        maximum = int(ceil(config.max * ratio))

        n_rows = maximum - minimum

        width = max(map(len, sequences))

        return cls(ratio, minimum, maximum, n_rows, width)