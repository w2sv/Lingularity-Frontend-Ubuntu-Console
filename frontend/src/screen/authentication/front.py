from typing import Tuple

from frontend.src.utils import query, output
from frontend.src.utils import view
from frontend.src.screen.authentication import login, sign_up
from frontend.src.screen.authentication._utils import authentication_screen_renderer
from frontend.src.screen._action_option import Option, Options


@view.creator(title=frontend.src.utils.view.terminal.DEFAULT_TITLE, banner_args=('lingularity/5line-oblique', 'blue'))
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

    selection = query.relentlessly('', indentation_percentage=0.49, options=AUTHENTICATION_OPTIONS.keywords)

    if authentication_result := AUTHENTICATION_OPTIONS[selection].__call__():
        return authentication_result
    return __call__()
