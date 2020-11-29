import os

from termcolor import colored

from frontend.utils import output, view


def display_signum():
    output.centered("W2SV", view.VERTICAL_OFFSET)


def display_sentence_data_reference():
    output.centered("Sentence data originating from the Tatoeba Project to be found at "
                    f"{colored('http://www.manythings.org/anki', 'red')}", view.VERTICAL_OFFSET)


USER_ENCRYPTION_FILE_PATH = f'{os.getcwd()}/.logged_in_user'


def remove_cached_user_login():
    os.remove(USER_ENCRYPTION_FILE_PATH)
