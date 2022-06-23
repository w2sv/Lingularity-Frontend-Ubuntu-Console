from typing import Optional, Tuple
from functools import wraps

from termcolor import colored

from frontend.utils import DATA_DIR_PATH, output
from frontend.utils.view import terminal


VERTICAL_OFFSET = '\n' * 2


def creator(title: Optional[str] = None,
            header: Optional[str] = None,
            banner_args: Optional[Tuple[str, str]] = None,
            vertical_offsets: int = 1):

    """ Decorator for functions creating new screen view,
        serving both documentation purposes as well as initializing the latter
        by
            clearing screen,
            outputting vertical offset(s),

            and eventually:
              displaying passed header/colored banner with vertical offset

        Args:
            title: terminal title
            header: displayed in centered manner in case of reception
            banner_args: tuple of relative banner path from banner directory, banner color
            vertical_offsets: inserted after banner/header """

    def outer_wrapper(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            # clear screen, output vertical offsets
            output.clear_screen()

            for _ in range(vertical_offsets):
                print(VERTICAL_OFFSET)

            # set title if applicable
            if title is not None:
                terminal.set_title(title=title)

            # display banner or header with consecutive vertical offset
            if any([header, banner_args]):
                if banner_args is not None:
                    _display_banner(kind=banner_args[0], color=banner_args[1])

                elif header is not None:
                    output.centered(header)

                print(VERTICAL_OFFSET, end='')

            return function(*args, **kwargs)
        return wrapper
    return outer_wrapper


def _display_banner(kind: str, color='red'):
    with open(DATA_DIR_PATH / 'banners' / f'{kind}.txt') as f:
        output.centered(colored(f.read(), color))