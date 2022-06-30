from frontend.src.utils import output
from frontend.src.utils import view
from frontend.src.screen.exit._error_exit_screen import error_exit_screen


@view.creator(title=frontend.src.utils.view.terminal.DEFAULT_TITLE, banner_args=('lingularity/ticks-slant', 'blue'), vertical_offsets=2)
@output.cursor_hider
@error_exit_screen
def __call__():
    output.centered('Lingularity relies on an internet connection in order to retrieve and store data.')
    output.centered('Please establish one and restart the program.')
