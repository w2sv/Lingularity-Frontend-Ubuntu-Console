from typing import Iterable, Optional, Callable, Tuple, Any
import time
import cursor

from lingularity.frontend.console.utils.output import clear_screen, erase_lines, centered_print


INDISSOLUBILITY_MESSAGE = "Couldn't resolve input"


def resolve_input(_input: str, options: Iterable[str]) -> Optional[str]:
    options_starting_on_input = list(filter(lambda option: option.lower().startswith(_input.lower()), options))

    if len(options_starting_on_input) == 1:
        return options_starting_on_input[0]
    elif _input in options_starting_on_input:
        return _input
    return None


def recurse_on_invalid_input(function: Callable,
                             message: str,
                             n_deletion_lines: int,
                             sleep_duration=1.0,
                             args: Optional[Tuple[Any, ...]] = None):
    if args is None:
        args = ()

    indissolubility_output(n_deletion_lines, message, sleep_duration)

    return function(*args)


def indissolubility_output(n_deletion_lines: int, message=INDISSOLUBILITY_MESSAGE, sleep_duration=1.0):
    centered_print(message.upper())
    cursor.hide()
    time.sleep(sleep_duration)

    if n_deletion_lines == -1:
        clear_screen()
    else:
        erase_lines(n_deletion_lines)

    cursor.show()


def recurse_on_unresolvable_input(function: Callable, n_deletion_lines, args: Optional[Tuple[Any, ...]] = None):
    return recurse_on_invalid_input(
        function=function,
        message=INDISSOLUBILITY_MESSAGE,
        n_deletion_lines=n_deletion_lines,
        args=args
    )
