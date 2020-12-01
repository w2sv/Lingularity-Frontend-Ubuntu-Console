import time

from frontend.utils import output


_INDISSOLUBILITY_MESSAGE = "COULDN'T RESOLVE INPUT"


@output.cursor_hider
def indicate_erroneous_input(message=_INDISSOLUBILITY_MESSAGE, n_deletion_lines=0, sleep_duration=1.0):
    """ - Display message communicating indissolubility reason,
        - freeze program for sleep duration
        - erase n_deletion_rows last rows or clear screen if n_deletion_rows = -1 """

    output.centered(f'\n{message}')

    time.sleep(sleep_duration)

    if n_deletion_lines == -1:
        output.clear_screen()
    else:
        output.erase_lines(n_deletion_lines + 1)
