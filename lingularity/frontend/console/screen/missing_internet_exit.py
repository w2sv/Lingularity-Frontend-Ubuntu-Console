import sys
import time

from lingularity.frontend.console.utils import output, view


@view.view_creator(title='Acquire Languages the Litboy Way', banner_kind='isometric2', banner_color='blue')
@output.cursor_hider
def __call__():
    print('\n' * 10)
    output.centered_print('\nLingularity relies on an internet connection in order to retrieve and store data. Please establish one and restart the program.')
    time.sleep(5)
    sys.exit(0)
