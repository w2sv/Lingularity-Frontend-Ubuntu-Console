from termcolor import colored

from frontend.utils import output, view


def display_signum():
    output.centered("W2SV", view.VERTICAL_OFFSET)


def display_sentence_data_reference():
    output.centered("Sentence data originating from the Tatoeba Project to be found at "
                    f"{colored('http://www.manythings.org/anki', 'red')}", view.VERTICAL_OFFSET)
