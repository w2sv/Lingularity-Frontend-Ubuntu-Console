from frontend.utils import view, output
from frontend.screen.exit._error_exit_screen import error_exit_screen


@view.creator(title=view.terminal.DEFAULT_TITLE, banner_args=('lingularity/ticks-slant', 'blue'), vertical_offsets=2)
@output.cursor_hider
@error_exit_screen
def __call__():
    output.centered('Lingularity relies on an internet connection in order to retrieve and store data.')
    output.centered('Please establish one and restart the program.')
