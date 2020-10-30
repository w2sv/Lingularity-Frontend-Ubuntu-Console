from typing import Iterable, Optional, Callable, Tuple, Any, Sequence
import time

from lingularity.frontend.utils import output

_INDISSOLUBILITY_MESSAGE = "COULDN'T RESOLVE INPUT"
HORIZONTAL_OFFSET = output.column_percentual_indentation(percentage=0.1)

# ------------------
# Input Resolution
# ------------------
def _resolve_input(_input: str, options: Iterable[str]) -> Optional[str]:
    options_starting_on_input = list(filter(lambda option: option.lower().startswith(_input.lower()), options))

    if len(options_starting_on_input) == 1:
        return options_starting_on_input[0]
    elif _input in options_starting_on_input:
        return _input
    return None


@output.cursor_hider
def _indicate_indissolubility(n_deletion_lines: int, message=_INDISSOLUBILITY_MESSAGE, sleep_duration=1.0):
    """ - Display message communicating indissolubility reason,
        - freeze program for sleep duration
        - erase n_deletion_lines last output output lines or clear screen if n_deletion_lines = -1 """

    output.centered_print(message)

    time.sleep(sleep_duration)

    if n_deletion_lines == -1:
        output.clear_screen()
    else:
        output.erase_lines(n_deletion_lines)


# ------------------
# Callable Repetition
# ------------------
def repeat(function: Callable,
           n_deletion_lines: int,
           message=_INDISSOLUBILITY_MESSAGE,
           sleep_duration=1.0,
           args: Tuple[Any, ...] = ()):

    """ Args:
            function: callable to be repeated
            n_deletion_lines: output output lines to be deleted, if -1 screen will be cleared
            message: message to be displayed, communicating mistake committed by user because of which
                repetition had to be triggered
            sleep_duration: program sleep duration in ms
            args: function args which it will be provided with when being repeated
        Returns:
            result of function provided with args """

    _indicate_indissolubility(n_deletion_lines, message, sleep_duration)

    return function(*args)


def relentlessly(query_message: str, options: Sequence[str]) -> str:
    if (option_selection := _resolve_input(input(query_message), options=options)) is None:
        return repeat(relentlessly, n_deletion_lines=2, args=(query_message, options))
    return option_selection
