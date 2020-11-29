import time

from frontend.utils import view, output


@view.creator(title=view.terminal.DEFAULT_TITLE, banner_args=('lingularity/ticks-slant', 'blue'), vertical_offsets=2)
@output.cursor_hider
def __call__():
    output.centered('Lingularity relies on an internet connection in order to retrieve and store data. '
                    'Please establish one and restart the program.')
    time.sleep(5)
    print(view.VERTICAL_OFFSET)
