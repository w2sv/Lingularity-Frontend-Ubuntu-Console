from ._utils import _terminal_columns, _terminal_lines


def column_percentual_indentation(percentage: float) -> str:
    """ Args:
            percentage: in decimal form """

    return ' ' * int(_terminal_columns() * percentage)


def row_percentual_indentation(percentage: float) -> str:
    """ Args:
            percentage: in decimal form """

    return "\n" * int(_terminal_lines() * percentage)
