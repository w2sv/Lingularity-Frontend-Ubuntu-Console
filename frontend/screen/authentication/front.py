from typing import Tuple

from termcolor import colored

from frontend.utils import query, output, view
from frontend.screen.authentication import login, sign_up
from frontend.screen.authentication._utils import authentication_screen


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

    def _colored(text):
        return colored(text, "red")

    output.centered(f'({_colored("L")}){_colored("og in")}{output.column_percentual_indentation(0.08)}({_colored("S")}){_colored("ign Up")}')
    print(output.EMPTY_ROW)

    selection = query.relentlessly('', options=['log in', 'sign up'], indentation_percentage=0.49)
    return _SELECTION_2_SCREEN[selection].__call__()  # type: ignore
