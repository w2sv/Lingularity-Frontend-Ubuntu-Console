"""Module to generate ascii charts.
This module provides a single function `plot` that can be used to generate an
ascii chart from a sequences of numbers. The chart can be configured via several
options to tune the output.
"""

from __future__ import annotations
from typing import *
from math import isnan
import re

from frontend.asciichartpy.config import Config, _is_numeric
from frontend.asciichartpy.params import Params
from frontend.asciichartpy.types import _Sequences
from frontend.asciichartpy import colors


def colored(chart: str, color: str) -> str:
    if not color:
        return chart
    return color + chart + colors.RESET


_PLOT_SEGMENTS = ['┼', '┤', '╶', '╴', '─', '╰', '╭', '╮', '╯', '│', '┬']


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

    if config.display_x_axis:
        _add_x_axis(chart, config)

    return chart


def _add_y_axis(chart: List[str], config: Config, params: Params):
    divisor = [1, params.n_rows][bool(params.n_rows)]

    for i in range(params.min, params.max + 1):
        label = config.format.format(config.max - ((i - params.min) * config.interval / divisor))
        chart[i - params.min][max(config.offset - len(label), 0)] = label
        chart[i - params.min][config.offset - 1] = _PLOT_SEGMENTS[[1, 0][i == 0]]


def _add_sequences(sequences: _Sequences, chart: List[str], config: Config, params: Params):

    def scaled(value: float):
        clamped_value = min(max(value, config.min), config.max)
        return int(round(clamped_value * params.ratio) - params.min)

    for i, sequence in enumerate(sequences):
        color = config.colors[i % len(config.colors)]

        if _is_numeric(sequence[0]):
            chart[params.n_rows - scaled(sequence[0])][config.offset - 1] = colored(_PLOT_SEGMENTS[0], color)

        # add symbols corresponding to singular sequences
        for j in range(len(sequence) - 1):
            value = sequence[j]
            following_value = sequence[j + 1]

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

                chart[params.n_rows - row_subtrahend][j + config.offset] = colored(symbol, color)

            else:
                if y0 > y1:
                    symbol_y0 = _PLOT_SEGMENTS[7]
                    symbol_y1 = _PLOT_SEGMENTS[5]
                else:
                    symbol_y0 = _PLOT_SEGMENTS[8]
                    symbol_y1 = _PLOT_SEGMENTS[6]

                chart[params.n_rows - y0][j + config.offset] = colored(symbol_y0, color)
                chart[params.n_rows - y1][j + config.offset] = colored(symbol_y1, color)

                start = min(y0, y1) + 1
                end = max(y0, y1)
                for y in range(start, end):
                    chart[params.n_rows - y][j + config.offset] = colored(_PLOT_SEGMENTS[9], color)


def _add_x_axis(chart: List[str], config: Config):
    _SEGMENT_2_X_AXIS_TOUCHING_SUBSTITUTE = {
        '┤': '┼',
        '─': '┬',
        '╰': '├',
        '╯': '┤',
        '': ''
    }

    ANSI_ESCAPE_PATTERN = re.compile(r'\x1b[^m]*m')

    def _extract_color(chart_parcel: str) -> str:
        if len((ansi_sequences := re.findall(ANSI_ESCAPE_PATTERN, chart_parcel))):
            return ansi_sequences[0]
        return ''

    def is_data_point(point_index: int) -> bool:
        return point_index % (config.horizontal_point_spacing + 1) == 0

    last_row = chart[-1]

    if not _extract_color(last_row[config.offset - 1]):
        last_row[config.offset - 1] = _PLOT_SEGMENTS[0]

    for i, segment in enumerate(last_row[config.offset:]):
        _is_data_point = is_data_point(i + 1)

        if segment == ' ':
            if _is_data_point:
                last_row[i + config.offset] = _PLOT_SEGMENTS[-1]
            else:
                last_row[i + config.offset] = _PLOT_SEGMENTS[4]
        elif _is_data_point:
            if color := _extract_color(segment):
                segment = re.split(ANSI_ESCAPE_PATTERN, segment)[1]

            last_row[i + config.offset] = color + _SEGMENT_2_X_AXIS_TOUCHING_SUBSTITUTE[segment] + colors.RESET

    for row_index in range(len(chart) - 1):
        if (last_column_segment := chart[row_index][-2]) != ' ':
            chart[row_index][-1] = _extract_color(last_column_segment) + _PLOT_SEGMENTS[4] + colors.RESET


if __name__ == '__main__':
    print(plot([2, 6, 17, 0, 0, 21, 11, 0, 0, 0, 2, 0, 27, 33, 15], config=Config(
        horizontal_point_spacing=5,
        offset=30,
        colors=[colors.RED],
        display_x_axis=True,
        height=15
    )))
