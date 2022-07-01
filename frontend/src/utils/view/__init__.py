from __future__ import annotations

from dataclasses import dataclass
from functools import wraps

from backend.src.utils.io import PathLike
from termcolor import colored

from frontend.src.paths import RESOURCE_DIR_PATH
from frontend.src.utils import output
from frontend.src.utils.view import terminal


VERTICAL_OFFSET = '\n' * 2


@dataclass(frozen=True)
class Banner:
    kind: PathLike
    color: str

    def display(self):
        with open(RESOURCE_DIR_PATH / 'banners' / f'{self.kind}.txt') as f:
            output.centered(colored(f.read(), self.color))


def creator(title: str | None = None,
            header: str | None = None,
            banner: Banner | None = None,
            vertical_offsets: int = 1,
            additional_vertical_offset: str | None = None):

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
            banner: tuple of relative banner path from banner directory, banner highlight_color
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
            if any([header, banner]):
                if banner is not None:
                    banner.display()
                elif header is not None:
                    output.centered(header)

                print(VERTICAL_OFFSET, end='')
                if additional_vertical_offset:
                    print(additional_vertical_offset)

            return function(*args, **kwargs)
        return wrapper
    return outer_wrapper