import datetime
import random

from termcolor import colored

from frontend.src.utils import output, view
from frontend.src.utils.view import Banner, terminal


def _day_of_the_month() -> int:
    return int(datetime.datetime.today().strftime('%d'))


@view.creator(
    title=terminal.DEFAULT_TERMINAL_TITLE,
    banner=Banner(random.choice(['lingularity/slant-relief', 'lingularity/sub-zero']), 'cyan')
)
def __call__():
    display_signum()
    display_sentence_data_reference()


def display_signum():
    output.centered("W2SV", view.VERTICAL_OFFSET)


def display_sentence_data_reference():
    output.centered("Sentence data originating from the Tatoeba Project to be found at "
                    f"{colored('https://www.manythings.org/anki', 'red')}", view.VERTICAL_OFFSET)
