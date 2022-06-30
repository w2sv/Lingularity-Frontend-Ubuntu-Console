from typing import Iterable, List, Optional, Sequence

from backend.src.utils.iterables import longest_value

from ._utils import _terminal_columns, ansi_escape_code_stripped
from .undoing import LineCounter


def centering_indentation(row: str) -> str:
    return " " * ((_terminal_columns() - len(ansi_escape_code_stripped(row))) // 2)


def centered(*print_elements: str, end='\n', line_counter: Optional[LineCounter] = None):
    printer = [print, line_counter][bool(line_counter)]
    assert printer is not None

    for i, print_element in enumerate(print_elements):
        if '\n' in print_element:

            # print newlines if print_element exclusively comprised of them
            if len(set(print_element)) == 1:
                for new_line_char in print_element:
                    printer(new_line_char, end='')

            # otherwise print writing in between newlines in uniformly indented manner
            else:
                distinct_lines = print_element.split('\n')
                indentation = block_centering_indentation(distinct_lines)

                for line in distinct_lines:
                    printer(indentation + line)

        else:
            printer(centering_indentation(print_element) + print_element, end=['\n', end][i == len(print_elements) - 1])


# ------------------
# Block Centering
# ------------------
def align(column1: Sequence[str], column2: Sequence[str]) -> List[str]:
    """ Args:
            column1 to be of equal length as column2

        Joins rows of column1 and column2 such that respective column beginnings
        vertically aligned """

    max_length_first_column_element = max(map(len, column1))
    return [f"{' ' * (max_length_first_column_element - len(column1[i]) + 1)}".join([column1[i], column2[i]]) for i in range(len(column1))]


def block_centering_indentation(output_block: Iterable[str]) -> str:
    """ Returns:
            indentation determined by length of longest output output row comprised by output_block,
            enabling center_message positioning of the aforementioned row and the others to start on the same
            output column, resulting in an uniform writing appearance """

    return centering_indentation(longest_value(output_block))
