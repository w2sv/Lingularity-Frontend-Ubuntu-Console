import time

from frontend.utils import view, output


@view.creator(title='Acquire Languages the Litboy Way', banner_args=('lingularity/ticks-slant', 'blue'), vertical_offsets=2)
@output.cursor_hider
def __call__():
    output.centered('An error occurred. Please restart the program.')
    time.sleep(5)
    print(view.VERTICAL_OFFSET)
