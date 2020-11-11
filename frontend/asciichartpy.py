"""Module to generate ascii charts.
This module provides a single function `plot` that can be used to generate an
ascii chart from a sequences of numbers. The chart can be configured via several
options to tune the output.
"""

from __future__ import annotations
from typing import *
from math import ceil, floor, isnan, inf
import itertools
from dataclasses import dataclass


black = "\033[30m"
red = "\033[31m"
green = "\033[32m"
yellow = "\033[33m"
blue = "\033[34m"
magenta = "\033[35m"
cyan = "\033[36m"
lightgray = "\033[37m"
default = "\033[39m"
darkgray = "\033[90m"
lightred = "\033[91m"
lightgreen = "\033[92m"
lightyellow = "\033[93m"
lightblue = "\033[94m"
lightmagenta = "\033[95m"
lightcyan = "\033[96m"
white = "\033[97m"
reset = "\033[0m"


def colored(chart: str, color: str) -> str:
    if not color:
        return chart
    return color + chart + reset


_Sequences = List[Sequence[float]]


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

        width = max(map(len, sequences)) + config.offset

        return cls(ratio, minimum, maximum, n_rows, width)


_PLOT_SEGMENTS = ['┼', '┤', '╶', '╴', '─', '╰', '╭', '╮', '╯', '│', '┬']
_SEGMENT_2_X_AXIS_TOUCHING_SUBSTITUTE = {
    '┤': '┼',
    '─': '┬',
    '╰': '├',
    '╯': '┤'
}


def plot(*sequences: Sequence[float], config=Config()) -> str:
    sequences = list(sequences)  # type: ignore

    config.process(sequences)
    sequences = config.padded_sequences(sequences)

    return '\n'.join([''.join(row).rstrip() for row in _get_chart(sequences, config)])


def _get_chart(sequences: _Sequences, config: Config) -> List[str]:
    params = Params.compute(sequences, config)

    chart = [[' '] * params.width for _ in range(params.n_rows + 1)]
    _add_y_axis(chart, config, params)
    _add_sequences(sequences, chart, config, params)

    return chart

def _add_y_axis(chart: List[str], config: Config, params: Params):
    for y in range(params.minimum, params.maximum + 1):
        label = config.format.format(params.maximum - ((y - params.minimum) * config.interval / [1, params.n_rows][bool(params.n_rows)]))
        chart[y - params.minimum][max(config.offset - len(label), 0)] = label
        chart[y - params.minimum][config.offset - 1] = _PLOT_SEGMENTS[0] if y == 0 else _PLOT_SEGMENTS[1]  # zero tick mark


def _add_sequences(sequences: _Sequences, chart: List[str], config: Config, params: Params):

    def scaled(value: float):
        clamped_value = min(max(value, params.minimum), params.maximum)
        return int(round(clamped_value * params.ratio) - params.minimum)

    def is_data_point(point_index: int) -> bool:
        return bool(point_index) and point_index % ((config.horizontal_point_spacing or 0) + 1) == 0

    # first value is a tick mark across the y-axis
    if _is_numeric(sequences[0][0]):
        symbol = _PLOT_SEGMENTS[0]
        chart[params.n_rows - scaled(sequences[0][0])][config.offset - 1] = symbol

    for i, series_i in enumerate(sequences):
        color = config.colors[i % len(config.colors)]

        # add symbols corresponding to singular sequences
        for j in range(len(series_i) - 1):

            # add x-axis segment
            if config.display_x_axis:
                if is_data_point(j):
                    axis_symbol = _PLOT_SEGMENTS[-1]
                else:
                    axis_symbol = _PLOT_SEGMENTS[4]

                chart[-1][j + config.offset] = axis_symbol

            value = series_i[j]
            following_value = series_i[j + 1]

            symbol_index: int = None  # type: ignore
            row_subtrahend: int = None  # type: ignore

            if isnan(value) and isnan(following_value):
                continue

            if isnan(value) and _is_numeric(following_value):
                symbol_index, row_subtrahend = 2, scaled(following_value)

            elif _is_numeric(value) and isnan(following_value):
                symbol_index, row_subtrahend = 3, scaled(value)

            elif (y0 := scaled(value)) == (y1 := scaled(following_value)):
                symbol_index, row_subtrahend = 4, y0

            if symbol_index is not None:
                symbol = _PLOT_SEGMENTS[symbol_index]

                if params.n_rows - row_subtrahend == params.n_rows and config.display_x_axis and is_data_point(j):
                    symbol = _SEGMENT_2_X_AXIS_TOUCHING_SUBSTITUTE[symbol]

                chart[params.n_rows - row_subtrahend][j + config.offset] = colored(symbol, color)

            else:
                if y0 > y1:
                    symbol_y0 = _PLOT_SEGMENTS[7]
                    symbol_y1 = _PLOT_SEGMENTS[5]
                else:
                    symbol_y0 = _PLOT_SEGMENTS[8]
                    symbol_y1 = _PLOT_SEGMENTS[6]

                if params.n_rows - y0 == params.n_rows and config.display_x_axis and is_data_point(j):
                    symbol_y0 = _SEGMENT_2_X_AXIS_TOUCHING_SUBSTITUTE[symbol_y0]

                chart[params.n_rows - y0][j + config.offset] = colored(symbol_y0, color)
                chart[params.n_rows - y1][j + config.offset] = colored(symbol_y1, color)

                start = min(y0, y1) + 1
                end = max(y0, y1)
                for y in range(start, end):
                    chart[params.n_rows - y][j + config.offset] = colored(_PLOT_SEGMENTS[9], color)

        if config.display_x_axis:
            chart[-1][-1] = _PLOT_SEGMENTS[-1]
            chart[params.n_rows-y1][-1] = colored(_PLOT_SEGMENTS[4], color)

            chart[-1][config.offset - 1] = _PLOT_SEGMENTS[0]


def _is_numeric(n: float) -> bool:
    return not isnan(n)


def _fill_points(start: float, end: float, n_points: int) -> List[float]:
    step_size = (end - start) / (n_points + 1)
    return list(itertools.accumulate([start] + [step_size] * n_points))[1:]


def _contains_unique_value(sequence: Iterable[Any]) -> bool:
    return len(set(sequence)) == 1


if __name__ == '__main__':
    print(plot([9] + list(range(4, 7)), config=Config(
        colors=[red],
        horizontal_point_spacing=3,
        display_x_axis=True
    )))
