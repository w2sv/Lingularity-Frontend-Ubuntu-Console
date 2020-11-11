from typing import Optional, Sequence, List, Any, Iterable
import itertools
from dataclasses import dataclass
from math import inf, isnan

from frontend.asciichartpy.types import _Sequences


@dataclass
class Config:
    min: float = inf
    max: float = -inf

    offset: int = 3
    height: Optional[float] = None

    colors: Sequence[Optional[str]] = (None,)
    format: str = '{:8.0f} '

    horizontal_point_spacing: int = 0
    display_x_axis: bool = True
    x_ticks: Optional[List[Any]] = None

    @property
    def interval(self) -> float:
        return self.max - self.min

    @property
    def ratio(self) -> float:
        return self.height / [1, self.interval][self.interval > 0]

    def process(self, sequences: _Sequences):
        self.min = min(self.min, min(filter(_is_numeric, itertools.chain(*sequences))))
        self.max = max(self.max, max(filter(_is_numeric, itertools.chain(*sequences))))

        if self.min > self.max:
            raise ValueError('The min value cannot exceed the max value.')

        if self.height is None:
            self.height = self.interval

        if bool(self.x_ticks) and not _contains_unique_value(map(len, itertools.chain(self.x_ticks, *sequences))):
            raise ValueError('x_ticks and entirety of passed sequences have to be at length parity')

    def padded_sequences(self, sequences: _Sequences) -> _Sequences:
        """
        >>> config = Config(horizontal_point_spacing=2)
        >>> config.padded_sequences([list(range(4))])
        [[0, 0.3333333333333333, 0.6666666666666666, 1, 1.3333333333333333, 1.6666666666666665, 2, 2.3333333333333335, 2.666666666666667, 3]] """

        if self.horizontal_point_spacing:
            padded_sequences = []
            for sequence in sequences:
                padded_sequence = []
                for i in range(len(sequence[:-1])):
                    padded_sequence.append(sequence[i])
                    padded_sequence.extend(_fill_points(
                        start=sequence[i],
                        end=sequence[i + 1],
                        n_points=self.horizontal_point_spacing
                    ))
                padded_sequences.append(padded_sequence + [sequence[-1]])
            sequences = padded_sequences

        return sequences


def _is_numeric(n: float) -> bool:
    return not isnan(n)


def _fill_points(start: float, end: float, n_points: int) -> List[float]:
    step_size = (end - start) / (n_points + 1)
    return list(itertools.accumulate([start] + [step_size] * n_points))[1:]


def _contains_unique_value(sequence: Iterable[Any]) -> bool:
    return len(set(sequence)) == 1
