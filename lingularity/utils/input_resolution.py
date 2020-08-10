from typing import Iterable, Optional, Callable, List, Any
import time

from lingularity.utils.output_manipulation import clear_screen, erase_lines


def resolve_input(_input: str, options: Iterable[str]) -> Optional[str]:
    options_starting_on_input = list(filter(lambda option: option.startswith(_input), options))
    return options_starting_on_input[0] if len(options_starting_on_input) == 1 else None


def recurse_on_unresolvable_input(func: Callable, *args, **kwargs):
    print("Couldn't resolve input")
    time.sleep(1)
    clear_screen()
    return func(*args, **kwargs)


def recurse_on_invalid_input(func: Callable,
                             message: str,
                             n_deletion_lines: int,
                             args: Optional[List[Any]] = None,
                             indentation: Optional[str] = None):
    if args is None:
        args = []

    print(f'{indentation if indentation is not None else ""}{message}')
    time.sleep(1.5)
    erase_lines(n_deletion_lines)
    return func(*args)
