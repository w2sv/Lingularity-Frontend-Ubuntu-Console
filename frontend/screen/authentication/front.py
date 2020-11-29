from typing import Tuple

from frontend.utils import query, output, view
from frontend.screen.authentication import login, sign_up
from frontend.screen.authentication._utils import authentication_screen
from frontend.screen.ops import option


_SELECTION_2_SCREEN = {
    'log in': login,
    'sign up': sign_up
}


@view.creator(title=view.DEFAULT_TITLE, banner_args=('lingularity/5line-oblique', 'blue'))
@authentication_screen
def __call__() -> Tuple[str, bool]:
    """ Returns:
            username: str,
            is_new_user_flag: bool """

    output.centered(f'{option.color_description("Log In", keyword_index=0)}{output.column_percentual_indentation(0.08)}{option.color_description("Sign Up", keyword_index=0)}')
    output.empty_row()

    selection = query.relentlessly('', options=list(_SELECTION_2_SCREEN.keys()), indentation_percentage=0.49)
    return _SELECTION_2_SCREEN[selection].__call__()  # type: ignore
