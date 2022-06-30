from frontend.src.utils import output
from frontend.src.utils import view
from frontend.src.screen.exit._error_exit_screen import error_exit_screen
from frontend.src.utils.view.terminal import DEFAULT_TERMINAL_TITLE


@view.creator(title=DEFAULT_TERMINAL_TITLE, banner_args=('lingularity/ticks-slant', 'blue'), vertical_offsets=2)
@output.cursor_hider
@error_exit_screen
def __call__():
    output.centered('An error occurred. Please restart the program.')
