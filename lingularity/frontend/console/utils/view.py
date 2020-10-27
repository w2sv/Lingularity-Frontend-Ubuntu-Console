from typing import Optional
from functools import wraps
import os

from termcolor import colored

from lingularity.frontend.console.utils import output


DEFAULT_VERTICAL_VIEW_OFFSET = '\n' * 2


def view_creator(
        header: Optional[str] = None,
        title: Optional[str] = None,
        banner_kind: Optional[str] = None,
        banner_color: Optional[str] = None
):
    """ Decorator for functions creating new output view,
        serving both documentation purposes as well as initializing the latter
        by
            clearing screen,
            outputting vertical offset,

            and eventually:
              displaying passed header with vertical offset """

    def outer_wrapper(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            output.clear_screen()
            print(DEFAULT_VERTICAL_VIEW_OFFSET)

            if title is not None:
                set_terminal_title(title=title)

            if any([title, banner_kind]):
                if banner_kind is not None:
                    _display_banner(kind=banner_kind, color=banner_color)

                if header is not None:
                    output.centered_print(header)

                print(DEFAULT_VERTICAL_VIEW_OFFSET, end='')

            return function(*args, **kwargs)
        return wrapper
    return outer_wrapper


def _display_banner(kind: str, color='red'):
    banner = open(f'{os.getcwd()}/lingularity/frontend/console/resources/banners/{kind}.txt', 'r').read()
    output.centered_print(colored(banner, color))


def set_terminal_title(title: str):
    os.system(f'wmctrl -r :ACTIVE: -N "Lingularity - {title}"')
