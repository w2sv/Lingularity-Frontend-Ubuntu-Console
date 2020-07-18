from typing import Iterable, Optional, Callable
import time

from lingularity.utils.output_manipulation import clear_screen


def resolve_input(_input: str, options: Iterable[str]) -> Optional[str]:
    options_starting_on_input = list(filter(lambda option: option.startswith(_input), options))
    return options_starting_on_input[0] if len(options_starting_on_input) == 1 else None


def recurse_on_invalid_input(func: Callable, *args, **kwargs):
    print("Couldn't resolve input")
    time.sleep(1)
    clear_screen()
    return func(*args, **kwargs)
