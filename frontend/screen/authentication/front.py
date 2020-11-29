from typing import Tuple

from frontend.utils import query, output, view
from frontend.screen.authentication import login, sign_up
from frontend.screen.authentication._utils import authentication_screen
from frontend.screen._action_option import Option, Options


@view.creator(title=view.terminal.DEFAULT_TITLE, banner_args=('lingularity/5line-oblique', 'blue'))
@authentication_screen
def __call__() -> Tuple[str, bool]:
    """ Returns:
            username: str,
            is_new_user_flag: bool """

    AUTHENTICATION_OPTIONS = Options([
        Option('Log In', callback=login),
        Option('Sign Up', callback=sign_up)
    ], inter_option_indentation=output.column_percentual_indentation(0.08))

    output.centered(AUTHENTICATION_OPTIONS.display_row, '\n')

    selection = query.relentlessly('', options=AUTHENTICATION_OPTIONS.keywords, indentation_percentage=0.49)

    if authentication_result := AUTHENTICATION_OPTIONS[selection].__call__():
        return authentication_result
    return __call__()
