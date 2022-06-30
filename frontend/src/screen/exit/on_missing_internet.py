from frontend.src.screen.exit._error_exit_screen import error_exit_screen
from frontend.src.utils import output, view
from frontend.src.utils.view import terminal


@view.creator(title=terminal.DEFAULT_TERMINAL_TITLE, banner_args=('lingularity/ticks-slant', 'blue'), vertical_offsets=2)
@output.cursor_hider
@error_exit_screen
def __call__():
    output.centered('Lingularity relies on an internet connection in order to retrieve and store data.')
    output.centered('Please establish one and restart the program.')
