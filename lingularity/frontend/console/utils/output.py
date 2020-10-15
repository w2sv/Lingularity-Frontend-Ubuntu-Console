from typing import Deque, Sequence, Pattern
import os
import sys
import platform
from collections import deque
import shutil
import re

_TAB_OUTPUT_LENGTH = 4


# ------------------
# Utils
# ------------------
_ANSI_ESCAPE: Pattern[str] = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def _ansi_escape_code_stripped(string: str) -> str:
    """ Returns:
            ANSI escape code stripped string. e.g. '[35mHello Görl![0m' -> 'Hello Görl!' """

    return _ANSI_ESCAPE.sub('', string)


def _output_length(string: str) -> int:
    """ Returns:
            length of terminal output which the passed string would produce """

    til_newline_substring = string[:string.find('\n')]
    return len(til_newline_substring) + til_newline_substring.count('\t') * (_TAB_OUTPUT_LENGTH - 1)


def _terminal_length() -> int:
    return int(shutil.get_terminal_size().columns)


# ------------------
# Clearing
# ------------------
def clear_screen():
    os.system('cls' if platform.system() == 'Windows' else 'clear')


def _erase_previous_line():
    sys.stdout.write("\033[F")
    sys.stdout.write("\033[K")


def erase_lines(n_lines: int):
    print('')
    [_erase_previous_line() for _ in range(n_lines + 1)]


# -----------------
# Redoable Printing
# -----------------
class RedoPrint:
    """ Class enabling (partial) redo of all previously
        stored print elements """

    def __init__(self):
        self._buffer: Deque[str] = deque()

    def __call__(self, *args, **kwargs):
        """ Buffer and display passed print elements """

        self._buffer.append(''.join(args))
        print(*args, **kwargs)

    def redo_partially(self, n_deletion_lines: int):
        """ Remove the first n_deletion_lines buffer elements and redo remaining content """

        erase_lines(self._n_buffered_terminal_rows)

        for _ in range(n_deletion_lines):
            self._buffer.popleft()

        self.redo()

    def redo(self):
        for line in self._buffer:
            print(line)

    @property
    def _n_buffered_terminal_rows(self) -> int:
        """ Returns:
                number of occupied terminal rows if currently stored buffer content
                were to be displayed """

        return len(self._buffer) + sum(map(lambda output: output.count('\n') + sum(self._n_additionally_occupied_terminal_rows(line) for line in output.split('\n')), self._buffer))

    @staticmethod
    def _n_additionally_occupied_terminal_rows(line: str) -> int:
        return _output_length(line) // _terminal_length()


# -----------------
# Centered Printing
# -----------------
def centered_print(*print_elements: str, end='\n'):
    for i, print_element in enumerate(print_elements):
        if '\n' in print_element:

            # print newlines if print_element exclusively comprised of them
            if len(set(print_element)) == 1:
                for new_line_char in print_element:
                    print(new_line_char, end='')

            # otherwise print writing in between newlines in uniformly indented manner
            else:
                distinct_lines = print_element.split('\n')
                indentation = centered_output_block_indentation(distinct_lines)

                for line in distinct_lines:
                    print(indentation + line)

        else:
            print(_indentation(len(_ansi_escape_code_stripped(print_element))) + print_element, end=end if i == len(print_elements) - 1 else '\n')


def centered_user_query_indentation(input_message: str) -> str:
    INPUT_SPACE_LENGTH = 8

    return _indentation(len(input_message + ' ' * INPUT_SPACE_LENGTH))


def centered_output_block_indentation(output_block: Sequence[str]) -> str:
    """ Returns:
            indentation determined by length of longest terminal output row comprised by output_block,
            enabling centered positioning of the aforementioned row and the others to start on the same
            terminal column, resulting in an uniform writing appearance """

    return _indentation(max((len(line) for line in map(_ansi_escape_code_stripped, output_block))))


def _indentation(line_length: int) -> str:
    return " " * ((_terminal_length() - line_length) // 2)
