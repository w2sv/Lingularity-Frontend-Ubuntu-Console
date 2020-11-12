from typing import Union, Deque, List
from abc import ABC
from collections import deque

from .clearing import erase_lines
from ._utils import _output_length, _terminal_columns


class LineCounter(ABC):
    """ Interface for classes being capable of buffering the output
        passed to them and counting the number of output output rows
        the output of the aforementioned resulted in """

    def __init__(self, buffer_container: Union[List, Deque]):
        self._buffer: Union[List, Deque] = buffer_container
        self._append_to_last_element: bool = False

    @property
    def _n_buffered_terminal_rows(self) -> int:
        """ Returns:
                number of occupied output rows if currently stored buffer content
                were to be displayed """

        return sum(map(self._n_comprised_terminal_output_rows, self._buffer))

    @staticmethod
    def _n_comprised_terminal_output_rows(buffer_element: str) -> int:
        newline_delimited_rows = buffer_element.split('\n')
        return len(newline_delimited_rows) + sum(map(LineCounter._n_additionally_occupied_terminal_rows, newline_delimited_rows))

    @staticmethod
    def _n_additionally_occupied_terminal_rows(buffer_element: str) -> int:
        return _output_length(buffer_element) // _terminal_columns()

    def __call__(self, *args, end='\n'):
        """ Buffer and display passed print arguments """

        joined_output = ' '.join(args)

        # append joined output to last buffer element if
        # _append_to_last_element set to True,
        # otherwise append to buffer
        if self._append_to_last_element:
            self._buffer[-1] += joined_output
        else:
            self._buffer.append(joined_output)

        # reset flag
        self._append_to_last_element = False

        # display passed output
        print(joined_output, end=end)

        # enable appending of consecutive call arguments to last
        # buffer element if print end doesn't contain newline
        if '\n' not in end:
            self._append_to_last_element = True

    def __getattr__(self, item):
        return getattr(self._buffer, item)


class UndoPrint(LineCounter):
    """ Class enabling convenient undoing of received output """

    def __init__(self):
        super().__init__(buffer_container=[])

    def undo(self):
        erase_lines(self._n_buffered_terminal_rows)
        self._buffer.clear()
        self._append_to_last_element = False

    def add_lines_to_buffer(self, n_lines: int):
        # TODO

        self._append_to_last_element = False

        for _ in range(n_lines):
            self._buffer.append('')


class RedoPrint(LineCounter):
    """ Class enabling redoing of previously stored output """

    def __init__(self):
        super().__init__(buffer_container=deque())

    def redo_partially(self, n_deletion_lines: int):
        """ Remove the first n_deletion_lines buffer elements and
            redo the remaining buffer content """

        erase_lines(self._n_buffered_terminal_rows)

        for _ in range(n_deletion_lines):
            self._buffer.popleft()  # type: ignore

        self.redo()

    def redo(self):
        for line in self._buffer:
            print(line)
