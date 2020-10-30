import sys
import time

from lingularity.frontend.utils import view, output


@view.view_creator(title='Acquire Languages the Litboy Way', banner='lingularity/bloody', banner_color='blue')
@output.cursor_hider
def __call__():
    output.row_percentual_indentation(percentage=0.2)
    output.centered_print('Lingularity relies on an internet connection in order to retrieve and store data. '
                          'Please establish one and restart the program.')
    time.sleep(5)
    sys.exit(0)
