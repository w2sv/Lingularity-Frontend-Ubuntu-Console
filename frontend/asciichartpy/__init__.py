"""Module to generate ascii charts.
This module provides a single function `plot` that can be used to generate an
ascii chart from a sequences of numbers. The chart can be configured via several
options to tune the output.
"""

from __future__ import annotations
from typing import *
from math import isnan

from frontend.asciichartpy.config import Config, _is_numeric
from frontend.asciichartpy.params import Params
from frontend.asciichartpy.types import _Sequences


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


_PLOT_SEGMENTS = ['┼', '┤', '╶', '╴', '─', '╰', '╭', '╮', '╯', '│', '┬']


def plot(*sequences: Sequence[float], config=Config()) -> str:
    sequences = list(sequences)  # type: ignore

    config.process(sequences)
    sequences = config.padded_sequences(sequences)

    return '\n'.join([''.join(row).rstrip() for row in _get_chart(sequences, config)])


def _get_chart(sequences: _Sequences, config: Config) -> List[str]:
    params = Params.compute(sequences, config)

    chart = [[' '] * params.width for _ in range(params.n_rows + 1)]
    _add_sequences(sequences, chart, config, params)

    # if config.display_x_axis:
    #     _add_x_axis()

    _add_y_axis(chart, config, params)

    for i, row in enumerate(chart):
        chart[i] = [' '] * config.offset + row

    return chart

def _add_y_axis(chart: List[str], config: Config, params: Params):
    for i, row in enumerate(chart):
        label = config.format.format(params.maximum - ((i - params.minimum) * config.interval / [1, params.n_rows][bool(params.n_rows)]))
        chart[i - params.minimum] = [label] + [_PLOT_SEGMENTS[[1, 0][i == 0]]] + row


def _add_sequences(sequences: _Sequences, chart: List[str], config: Config, params: Params):

    def scaled(value: float):
        clamped_value = min(max(value, params.minimum), params.maximum)
        return int(round(clamped_value * params.ratio) - params.minimum)

    # first value is a tick mark across the y-axis
    # if _is_numeric(sequences[0][0]):
    #     chart[params.n_rows - scaled(sequences[0][0])][config.offset - 1] = _PLOT_SEGMENTS[0]

    for i, series_i in enumerate(sequences):
        color = config.colors[i % len(config.colors)]

        # add symbols corresponding to singular sequences
        for j in range(len(series_i) - 1):
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

                chart[params.n_rows - row_subtrahend][j] = colored(symbol, color)

            else:
                if y0 > y1:
                    symbol_y0 = _PLOT_SEGMENTS[7]
                    symbol_y1 = _PLOT_SEGMENTS[5]
                else:
                    symbol_y0 = _PLOT_SEGMENTS[8]
                    symbol_y1 = _PLOT_SEGMENTS[6]

                chart[params.n_rows - y0][j] = colored(symbol_y0, color)
                chart[params.n_rows - y1][j] = colored(symbol_y1, color)

                start = min(y0, y1) + 1
                end = max(y0, y1)
                for y in range(start, end):
                    chart[params.n_rows - y][j] = colored(_PLOT_SEGMENTS[9], color)


def _add_x_axis(chart: List[str], config: Config):
    _SEGMENT_2_X_AXIS_TOUCHING_SUBSTITUTE = {
        '┤': '┼',
        '─': '┬',
        '╰': '├',
        '╯': '┤'
    }

    def is_data_point(point_index: int) -> bool:
        return bool(point_index) and point_index % ((config.horizontal_point_spacing or 0) + 1) == 0

    last_row = chart[-1]

    # if is_data_point(j):
    #     axis_symbol = _PLOT_SEGMENTS[-1]
    # else:
    #     axis_symbol = _PLOT_SEGMENTS[4]
    #
    # chart[-1][j + config.offset] = axis_symbol
    #
    # if params.n_rows - row_subtrahend == params.n_rows and config.display_x_axis and is_data_point(j):
    #     symbol = _SEGMENT_2_X_AXIS_TOUCHING_SUBSTITUTE[symbol]
    #
    # if params.n_rows - y0 == params.n_rows and config.display_x_axis and is_data_point(j):
    #     symbol_y0 = _SEGMENT_2_X_AXIS_TOUCHING_SUBSTITUTE[symbol_y0]
    #
    # if config.display_x_axis:
    #     chart[-1][-1] = _PLOT_SEGMENTS[-1]
    #     chart[params.n_rows - y1][-1] = colored(_PLOT_SEGMENTS[4], color)
    #
    #     chart[-1][config.offset - 1] = _PLOT_SEGMENTS[0]


if __name__ == '__main__':
    print(plot([9] + list(range(4, 7)), config=Config(
        colors=[red],
        horizontal_point_spacing=3,
        display_x_axis=True,
        offset=2
    )))
