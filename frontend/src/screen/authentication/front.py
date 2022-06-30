from typing import Tuple

from frontend.src.screen.action_option import Option, Options
from frontend.src.screen.authentication import login, sign_up
from frontend.src.screen.authentication._utils import authentication_screen_renderer
from frontend.src.utils import output, view
from frontend.src.utils.query.repetition import query_relentlessly
from frontend.src.utils.view.terminal import DEFAULT_TERMINAL_TITLE


@view.creator(title=DEFAULT_TERMINAL_TITLE, banner_args=('lingularity/5line-oblique', 'blue'))
@authentication_screen_renderer
def __call__() -> Tuple[str, bool]:
    """ Returns:
            username: str,
            is_new_user_flag: bool """

    AUTHENTICATION_OPTIONS = Options([
        Option('Log In', callback=login),
        Option('Sign Up', callback=sign_up)
    ], inter_option_indentation=output.column_percentual_indentation(0.08))

    output.centered(AUTHENTICATION_OPTIONS.display_row, '\n')

    selection = query_relentlessly('', indentation_percentage=0.49, options=AUTHENTICATION_OPTIONS.keywords)

    if authentication_result := AUTHENTICATION_OPTIONS[selection].__call__():
        return authentication_result
    return __call__()
