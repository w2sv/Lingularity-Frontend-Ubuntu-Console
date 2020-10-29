import os
import time

from lingularity.frontend.utils import output

INTER_OPTION_INDENTATION = ' ' * 6


def maximize_console():
    os.system('wmctrl -r :ACTIVE: -b add,maximized_vert,maximized_horz')
    time.sleep(0.005)


def display_signum():
    output.centered_print("W2SV", '\n\n')


def display_sentence_data_reference():
    output.centered_print("Sentence data stemming from the Tatoeba Project to be found at"
                          " http://www.manythings.org/anki", '\n' * 2)
