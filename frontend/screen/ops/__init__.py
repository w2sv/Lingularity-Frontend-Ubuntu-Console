import subprocess
import time

from frontend.utils import output

INTER_OPTION_INDENTATION = ' ' * 6


def maximize_console():
    subprocess.call('wmctrl -r :ACTIVE: -b add,maximized_vert,maximized_horz', shell=True)


def display_signum():
    output.centered_print("W2SV", '\n\n')


def display_sentence_data_reference():
    output.centered_print("Sentence data stemming from the Tatoeba Project to be found at"
                          " http://www.manythings.org/anki", '\n' * 2)
