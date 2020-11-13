from typing import Optional, Sequence, List
import itertools
from dataclasses import dataclass, field
from math import inf, isfinite

from frontend.asciichartpy.types import _Sequences
from frontend.asciichartpy import colors


@dataclass
class Config:
    min: float = inf
    max: float = -inf
    y_value_spread: float = field(init=False)

    offset: int = 3
    height: int = 0

    colors: Sequence[str] = (colors.WHITE,)
    format: str = '{:8.0f} '

    horizontal_point_spacing: int = 0
    display_x_axis: bool = False
    x_labels: Optional[List[str]] = None

    title: Optional[str] = None
    ratio: float = field(init=False)

    def __post_init__(self):
        self.y_value_spread = self.max - self.min

    def process(self, sequences: _Sequences) -> _Sequences:
        self.min = min(self.min, min(filter(isfinite, itertools.chain(*sequences))))
        self.max = max(self.max, max(filter(isfinite, itertools.chain(*sequences))))

        if self.min > self.max:
            raise ValueError("min value shan't exceed max value.")

        if not self.height:
            self.height = int(self.y_value_spread)

        self.ratio = self.height / [1, self.y_value_spread][self.y_value_spread > 0]

        return self._padded_sequences(sequences)

    def _padded_sequences(self, sequences: _Sequences) -> _Sequences:
        """
        >>> config = Config(horizontal_point_spacing=2)
        >>> config._padded_sequences([list(range(4))])
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
            sequences = tuple(padded_sequences)

        return sequences


def _fill_points(start: float, end: float, n_points: int) -> List[float]:
    step_size = (end - start) / (n_points + 1)
    return list(itertools.accumulate([start] + [step_size] * n_points))[1:]
