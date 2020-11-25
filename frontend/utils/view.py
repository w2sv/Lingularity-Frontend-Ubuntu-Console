from typing import Optional
from functools import wraps
import subprocess
import os

from termcolor import colored

from frontend.utils import output


VERTICAL_OFFSET = '\n' * 2


def creator(
        header: Optional[str] = None,
        title: Optional[str] = None,
        banner: Optional[str] = None,
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
            print(VERTICAL_OFFSET)

            if title is not None:
                set_terminal_title(title=title)

            if any([title, banner]):
                if banner is not None:
                    _display_banner(kind=banner, color=banner_color)

                if header is not None:
                    output.centered(header)

                print(VERTICAL_OFFSET, end='')

            return function(*args, **kwargs)
        return wrapper
    return outer_wrapper


def _display_banner(kind: str, color='red'):
    banner = open(f'{os.getcwd()}/frontend/banners/{kind}.txt', 'r').read()
    output.centered(colored(banner, color))


def set_terminal_title(title: str):
    subprocess.run(['wmctrl', '-r', ':ACTIVE:', '-N', f'"Lingularity - {title}"'])


DEFAULT_TITLE = 'Acquire Languages the Litboy Way'
