from typing import Deque, Sequence
import os
import sys
import platform
from builtins import print as _print
from collections import deque
import shutil

import numpy as np

DEFAULT_VERTICAL_VIEW_OFFSET = '\n' * 2


def clear_screen():
    os.system('cls' if platform.system() == 'Windows' else 'clear')


def _erase_previous_line():
    sys.stdout.write("\033[F")
    sys.stdout.write("\033[K")


def erase_lines(n_lines: int):
    [_erase_previous_line() for _ in range(n_lines)]


class BufferPrint:
    def __init__(self):
        self._buffer: Deque[str] = deque()

    @property
    def n_buffered_lines(self) -> int:
        # TODO: add resilience regarding lines exceeding terminal length

        return self._buffer.__len__() + sum(map(lambda line: line.count('\n'), self._buffer))

    def __call__(self, *args, **kwargs):
        self._buffer.append(''.join(args))
        _print(*args, **kwargs)

    def partially_redo_buffered_output(self, n_lines_to_be_removed: int):
        erase_lines(self.n_buffered_lines)
        for _ in range(n_lines_to_be_removed):
            self._buffer.popleft()

        for line in self._buffer:
            print(line)


def _get_indentation(line_length: int) -> str:
    terminal_columns = int(shutil.get_terminal_size().columns)
    return " " * ((terminal_columns - line_length) // 2)


def get_max_line_length_based_indentation(output_block: Sequence[str]) -> str:
    return _get_indentation(len(output_block[np.argmax([len(l) for l in output_block])]))


def centered_print(*output: str, end='\n'):
    for i, output_element in enumerate(output):
        if '\n' in output_element:
            if set(output_element).__len__() == 1:
                print(output_element, end='')
            else:
                distinct_lines = output_element.split('\n')
                indentation = _get_indentation(line_length=max((len(line) for line in distinct_lines)))

                indented_output_block = map(lambda line: indentation + line, distinct_lines)
                for l in indented_output_block:
                    print(l)

        else:
            print(_get_indentation(len(output_element)) + output_element, end=end if i == len(output) - 1 else '\n')


def get_centered_input_query_indentation(input_message: str) -> str:
    INPUT_SPACE_LENGTH = 8

    return _get_indentation(len(input_message + ' ' * INPUT_SPACE_LENGTH))
