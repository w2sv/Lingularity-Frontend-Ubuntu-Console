from typing import Callable
from functools import wraps

import cursor

from .utils import ansi_escape_code_stripped
from .termcolor import colorize_chars
from .undoable_printing import LineCounter, UndoPrint, RedoPrint
from .clearing import clear_screen, erase_lines
from .termcolor import colorize_chars
from .centered_printing import (
    centered_query_indentation,
    centered_print,
    centered_print_indentation,
    centered_block_indentation,
    centered_input_query,
    align
)


SELECTION_QUERY_OUTPUT_OFFSET = '\n\t'


def cursor_hider(function: Callable):
    @wraps(function)
    def wrapper(*args, **kwargs):
        cursor.hide()
        result = function(*args, **kwargs)
        cursor.show()
        return result
    return wrapper
