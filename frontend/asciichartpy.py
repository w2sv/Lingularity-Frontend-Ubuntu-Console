"""Module to generate ascii charts.
This module provides a single function `plot` that can be used to generate an
ascii chart from a sequences of numbers. The chart can be configured via several
options to tune the output.
"""

from typing import *
from math import ceil, floor, isnan
import itertools


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


def colored(chart, color):
    if not color:
        return chart
    return color + chart + reset


def plot(*sequences: Iterable[float], cfg: Optional[Dict[str, str]] = None) -> List[str]:
    PLOT_SEGMENTS = ['┼', '┤', '╶', '╴', '─', '╰', '╭', '╮', '╯', '│', '┬']
    X_AXIS_TOUCHING_PLOT_SYMBOL_SUBSTITUTES = {
        '┤': '┼',
        '─': '┬',
        '╰': '├',
        '╯': '┤'
    }

    sequences = list(sequences)
    
    # ------PROCESS CONFIGURATION OPTIONS------
    cfg = cfg or {}

    colors = cfg.get('colors', [None])

    minimum = cfg.get('min', min(filter(_is_numeric, [j for i in sequences for j in i])))
    maximum = cfg.get('max', max(filter(_is_numeric, [j for i in sequences for j in i])))

    if minimum > maximum:
        raise ValueError('The min value cannot exceed the max value.')

    interval = maximum - minimum
    
    offset = cfg.get('offset', 3)
    height = cfg.get('height', interval)

    horizontal_point_spacing = cfg.get('horizontal_point_spacing', 0)
    if bool(horizontal_point_spacing):
        padded_series_i = []
        for i, series_i in enumerate(sequences):
            for j, series_i_j in enumerate(series_i[:-1]):
                padded_series_i.append(series_i_j)
                fill_points = _fill_points(series_i_j, series_i[j + 1], horizontal_point_spacing)
                padded_series_i.extend(fill_points)
            padded_series_i.append(series_i[-1])
            sequences[i] = padded_series_i[0:1] + padded_series_i[2:]

    display_x_axis = cfg.get('display_x_axis', False)

    x_ticks = cfg.get('x_ticks')
    if x_ticks is not None and not _contains_unique_value(map(len, itertools.chain(x_ticks, *sequences))):
        raise ValueError('x_ticks and entirety of passed sequences have to be at length parity')

    placeholder = cfg.get('format', '{:8.0f} ')

    # ------COMPUTE PARAMETERS------

    ratio = height / interval if interval > 0 else 1

    min2 = int(floor(minimum * ratio))
    max2 = int(ceil(maximum * ratio))

    n_rows = max2 - min2

    width = 0
    for i in range(0, len(sequences)):
        width = max(width, len(sequences[i]))
    width += offset

    chart = [[' '] * width for _ in range(n_rows + 1)]

    # ------ADD Y-AXIS WITH LABELS------
    for y in range(min2, max2 + 1):
        label = placeholder.format(maximum - ((y - min2) * interval / (n_rows if n_rows else 1)))
        chart[y - min2][max(offset - len(label), 0)] = label
        chart[y - min2][offset - 1] = PLOT_SEGMENTS[0] if y == 0 else PLOT_SEGMENTS[1]  # zero tick mark

    # ------ADD SEQUENCES------
    def scaled(value: float):
        clamped_value = min(max(value, minimum), maximum)
        return int(round(clamped_value * ratio) - min2)

    def is_data_point(point_index: int) -> bool:
        return point_index and point_index % ((horizontal_point_spacing or 0) + 1) == 0

    # first value is a tick mark across the y-axis
    if _is_numeric(sequences[0][0]):
        symbol = PLOT_SEGMENTS[0]
        chart[n_rows - scaled(sequences[0][0])][offset - 1] = symbol

    for i, series_i in enumerate(sequences):
        color = colors[i % len(colors)]

        # add symbols corresponding to singular sequences
        for j in range(len(series_i) - 1):

            # add x-axis segment
            if display_x_axis:
                if is_data_point(j):
                    axis_symbol = PLOT_SEGMENTS[-1]
                else:
                    axis_symbol = PLOT_SEGMENTS[4]

                chart[-1][j + offset] = axis_symbol

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
                symbol = PLOT_SEGMENTS[symbol_index]

                if n_rows - row_subtrahend == n_rows and display_x_axis and is_data_point(j):
                    symbol = X_AXIS_TOUCHING_PLOT_SYMBOL_SUBSTITUTES[symbol]

                chart[n_rows - row_subtrahend][j + offset] = colored(symbol, color)

            else:
                if y0 > y1:
                    symbol_y0 = PLOT_SEGMENTS[7]
                    symbol_y1 = PLOT_SEGMENTS[5]
                else:
                    symbol_y0 = PLOT_SEGMENTS[8]
                    symbol_y1 = PLOT_SEGMENTS[6]

                if n_rows - y0 == n_rows and display_x_axis and is_data_point(j):
                    symbol_y0 = X_AXIS_TOUCHING_PLOT_SYMBOL_SUBSTITUTES[symbol_y0]

                chart[n_rows - y0][j + offset] = colored(symbol_y0, color)
                chart[n_rows - y1][j + offset] = colored(symbol_y1, color)

                start = min(y0, y1) + 1
                end = max(y0, y1)
                for y in range(start, end):
                    chart[n_rows - y][j + offset] = colored(PLOT_SEGMENTS[9], color)

        if display_x_axis:
            chart[-1][-1] = PLOT_SEGMENTS[-1]
            chart[n_rows-y1][-1] = colored(PLOT_SEGMENTS[4], color)

            chart[-1][offset - 1] = PLOT_SEGMENTS[0]

    return '\n'.join([''.join(row).rstrip() for row in chart])


def _is_numeric(n: float) -> bool:
    return not isnan(n)


def _fill_points(start: float, end: float, n_points: int) -> List[float]:
    step_size = (end - start) / (n_points + 1)
    return list(itertools.accumulate([start] + [step_size] * n_points))[1:]


def _contains_unique_value(sequence: Sequence[Any]) -> bool:
    return len(set(sequence)) == 1


if __name__ == '__main__':
    print(plot([9] + list(range(4, 7)), cfg={
        'colors': [red],
        'horizontal_point_spacing': 3,
        'display_x_axis': True
    }))
