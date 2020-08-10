from typing import Iterable, Optional, Callable, List, Any
import time
import cursor

from lingularity.utils.output_manipulation import clear_screen, erase_lines, centered_print


def resolve_input(_input: str, options: Iterable[str]) -> Optional[str]:
    options_starting_on_input = list(filter(lambda option: option.startswith(_input), options))
    return options_starting_on_input[0] if len(options_starting_on_input) == 1 else None


def recurse_on_unresolvable_input(func: Callable, deletion_lines, *args, **kwargs):
    print("Couldn't resolve input")
    cursor.hide()
    time.sleep(1)
    clear_screen() if deletion_lines == -1 else erase_lines(deletion_lines)
    cursor.show()
    return func(*args, **kwargs)


def recurse_on_invalid_input(func: Callable,
                             message: str,
                             n_deletion_lines: int,
                             args: Optional[List[Any]] = None):
    if args is None:
        args = []

    centered_print(message.upper())
    cursor.hide()
    time.sleep(1.5)
    cursor.show()
    erase_lines(n_deletion_lines)
    return func(*args)
