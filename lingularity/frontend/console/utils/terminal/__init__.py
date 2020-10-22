from typing import Callable
from functools import wraps

import cursor

from .undoable_printing import LineCounter, UndoPrint, RedoPrint
from .clearing import clear_screen, erase_lines
from .centered_printing import (
    centered_query_indentation,
    centered_print,
    centered_print_indentation,
    centered_output_block_indentation,
    centered_input,
    allign
)


def cursor_hider(function: Callable):
    @wraps(function)
    def wrapper(*args, **kwargs):
        cursor.hide()
        result = function(*args, **kwargs)
        cursor.show()
        return result
    return wrapper
