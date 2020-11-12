import os
import subprocess

from termcolor import colored

from frontend.utils import output
from . import reference_language

INTER_OPTION_INDENTATION = ' ' * 7


def maximize_console():
    subprocess.call('wmctrl -r :ACTIVE: -b add,maximized_vert,maximized_horz', shell=True)


def display_signum():
    output.centered("W2SV", '\n' * 2)


def display_sentence_data_reference():
    output.centered("Sentence data stemming from the Tatoeba Project to be found at "
                    f"{colored('http://www.manythings.org/anki', 'red')}", '\n' * 2)


USER_ENCRYPTION_FILE_PATH = f'{os.getcwd()}/.logged_in_user'


def remove_user_from_disk():
    os.remove(USER_ENCRYPTION_FILE_PATH)
