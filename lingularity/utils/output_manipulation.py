from typing import Deque
import os
import sys
import platform
from builtins import print as _print
from collections import deque


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
    def n_comprised_lines(self) -> int:
        # TODO: add resilience regarding lines exceeding terminal length
        return self._buffer.__len__() + sum(map(lambda line: line.count('\n'), self._buffer))

    def __call__(self, *args, **kwargs):
        self._buffer.append(''.join(args))
        _print(*args, **kwargs)

    def partially_redo_buffered_output(self, n_lines_to_be_removed: int):
        erase_lines(self.n_comprised_lines)
        for _ in range(n_lines_to_be_removed):
            self._buffer.popleft()

        for line in self._buffer:
            print(line)
