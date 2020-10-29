from typing import Pattern
import re
import shutil


_TAB_OUTPUT_LENGTH = 4
_ANSI_ESCAPE_REGEX: Pattern[str] = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def ansi_escape_code_stripped(string: str) -> str:
    """ Returns:
            ANSI escape code stripped string

        >>> ansi_escape_code_stripped('[35mHello Görl![0m')
        'Hello Görl!' """

    return _ANSI_ESCAPE_REGEX.sub('', string)


def _output_length(string: str) -> int:
    """ Args:
            string: string free of '\n's

        Returns:
            length of output output which the passed string would produce """

    return len(ansi_escape_code_stripped(string)) + string.count('\t') * (_TAB_OUTPUT_LENGTH - 1)


def _terminal_columns() -> int:
    return int(shutil.get_terminal_size().columns)


def _terminal_lines() -> int:
    return int(shutil.get_terminal_size().lines)
