from typing import Deque, Sequence
import os
import sys
import platform
from builtins import print as _print
from collections import deque
import shutil

import numpy as np


DEFAULT_VERTICAL_VIEW_OFFSET = '\n' * 2
TERMINAL_LENGTH = int(shutil.get_terminal_size().columns)
TAB_LENGTH = 4


def clear_screen():
    os.system('cls' if platform.system() == 'Windows' else 'clear')


def _erase_previous_line():
    sys.stdout.write("\033[F")
    sys.stdout.write("\033[K")


def erase_lines(n_lines: int):
    print('')
    [_erase_previous_line() for _ in range(n_lines + 1)]


def _output_length(string: str) -> int:
    til_newline_substring = string[:string.find('\n')]
    return len(til_newline_substring) + til_newline_substring.count('\t') * (TAB_LENGTH - 1)


def _n_line_breaks(line: str) -> int:
    return _output_length(line) // TERMINAL_LENGTH


class BufferPrint:
    def __init__(self):
        self._buffer: Deque[str] = deque()

    @property
    def n_buffered_lines(self) -> int:
        return len(self._buffer) + sum(map(lambda output: output.count('\n') + sum(_n_line_breaks(line) for line in output.split('\n')), self._buffer))

    def __call__(self, *args, **kwargs):
        self._buffer.append(''.join(args))
        _print(*args, **kwargs)

    def output_buffer_content(self):
        for line in self._buffer:
            print(line)

    def partially_redo_buffer_content(self, n_deletion_lines: int):
        erase_lines(self.n_buffered_lines)

        for _ in range(n_deletion_lines):
            self._buffer.popleft()

        self.output_buffer_content()


def _get_indentation(line_length: int) -> str:
    return " " * ((TERMINAL_LENGTH - line_length) // 2)


def get_max_line_length_based_indentation(output_block: Sequence[str]) -> str:
    return _get_indentation(len(output_block[int(np.argmax([len(line) for line in output_block]))]))


def centered_print(*output: str, end='\n'):
    for i, output_element in enumerate(output):
        if '\n' in output_element:
            if len(set(output_element)) == 1:
                print(output_element, end='')
            else:
                distinct_lines = output_element.split('\n')
                indentation = _get_indentation(line_length=max((len(line) for line in distinct_lines)))

                indented_output_block = map(lambda line: indentation + line, distinct_lines)
                for line in indented_output_block:
                    print(line)

        else:
            print(_get_indentation(len(output_element)) + output_element, end=end if i == len(output) - 1 else '\n')


def get_centered_input_query_indentation(input_message: str) -> str:
    INPUT_SPACE_LENGTH = 8

    return _get_indentation(len(input_message + ' ' * INPUT_SPACE_LENGTH))
