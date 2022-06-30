from functools import lru_cache

from ._utils import _terminal_columns, _terminal_lines


_CASH_SIZE = 32


@lru_cache(maxsize=_CASH_SIZE)
def column_percentual_indentation(percentage: float) -> str:
    """ Args:
            percentage: in decimal form """

    return ' ' * int(_terminal_columns() * percentage)


@lru_cache(maxsize=_CASH_SIZE)
def row_percentual_indentation(percentage: float) -> str:
    """ Args:
            percentage: in decimal form """

    return '\n' * int(_terminal_lines() * percentage)


class IndentedPrint:
    def __init__(self, indentation: str):
        self._indentation = indentation

    def __call__(self, *args, **kwargs):
        print(self._indentation, *args, **kwargs)