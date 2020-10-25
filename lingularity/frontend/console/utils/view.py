from typing import Optional
from functools import wraps

from lingularity.frontend.console.utils.console import clear_screen, centered_print


DEFAULT_VERTICAL_VIEW_OFFSET = '\n' * 2


def view_creator(header: Optional[str] = None):
    """ Decorator for functions creating new console view,
        serving both documentation purposes as well as initializing the latter
        by
            clearing screen,
            outputting vertical offset,

            and eventually:
              displaying passed header with vertical offset """

    def outer_wrapper(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            clear_screen()
            print(DEFAULT_VERTICAL_VIEW_OFFSET)

            if header is not None:
                centered_print(header)
                print(DEFAULT_VERTICAL_VIEW_OFFSET, end='')

            return function(*args, **kwargs)
        return wrapper
    return outer_wrapper
