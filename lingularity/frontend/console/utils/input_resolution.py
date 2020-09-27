from typing import Iterable, Optional, Callable, List, Any
import time
import cursor

from lingularity.frontend.console.utils.output_manipulation import clear_screen, erase_lines, centered_print


def resolve_input(input_request_message: str, options: Iterable[str]) -> Optional[str]:
    _input = input(input_request_message)
    options_starting_on_input = list(filter(lambda option: option.lower().startswith(_input.lower()), options))

    if len(options_starting_on_input) == 1:
        return options_starting_on_input[0]
    elif _input in options_starting_on_input:
        return _input
    else:
        return None


def recurse_on_invalid_input(func: Callable,
                             message: str,
                             n_deletion_lines: int,
                             func_args: Optional[List[Any]] = None,
                             sleep_duration=1.5):
    if func_args is None:
        func_args = []

    centered_print(message.upper())
    cursor.hide()
    time.sleep(sleep_duration)

    if n_deletion_lines == -1:
        clear_screen()
    else:
        erase_lines(n_deletion_lines)

    cursor.show()
    return func(*func_args)


def recurse_on_unresolvable_input(func: Callable, n_deletion_lines, *func_args):
    return recurse_on_invalid_input(func, "Couldn't resolve input", n_deletion_lines, func_args, sleep_duration=1.0)
