from typing import Callable, Iterable, Iterator
from functools import wraps
from itertools import groupby

import cursor

from ._utils import ansi_escape_code_stripped
from .colorizing import colorize_chars
from .undoing import LineCounter, UndoPrint, RedoPrint
from .clearing import clear_screen, erase_lines
from .percentual_indenting import column_percentual_indentation, row_percentual_indentation
from .centering import (
    centered,
    centering_indentation,
    block_centering_indentation,
    align
)


def cursor_hider(function: Callable):
    """ Hides cursor for the duration of the execution
        of the decorated function and renders it visible
        again afterwards """

    @wraps(function)
    def wrapper(*args, **kwargs):
        cursor.hide()
        result = function(*args, **kwargs)
        cursor.show()
        return result
    return wrapper


def group_by_starting_letter(strings: Iterable[str], is_sorted: bool) -> Iterator[Iterator[str]]:
    """ Args:
            strings: to be grouped by starting letter, either already sorted or
            is_sorted: to be set to True
        Returns:
            Iterator of Iterators of strings starting on the same letter """

    if not is_sorted:
        strings = sorted(strings)

    return (v for _, v in groupby(strings, lambda element: element[0]))


def empty_row(times=1):
    for _ in range(times):
        print()
