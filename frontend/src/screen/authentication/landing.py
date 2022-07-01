from frontend.src.option import Option, OptionCollection
from frontend.src.screen.authentication import login, sign_up
from frontend.src.screen.authentication._utils import authentication_screen
from frontend.src.utils import output, view
from frontend.src.utils.prompt.repetition import prompt_relentlessly
from frontend.src.utils.view import Banner
from frontend.src.utils.view.terminal import DEFAULT_TERMINAL_TITLE


@view.creator(title=DEFAULT_TERMINAL_TITLE, banner=Banner('lingularity/5line-oblique', 'blue'))
@authentication_screen
def __call__() -> tuple[str, bool]:
    """ Returns:
            username: str,
            is_new_user_flag: bool """

    options = OptionCollection(
        [
            Option('log', 'Log In', callback=login.__call__),
            Option('sign', 'Sign Up', callback=sign_up.__call__)
        ]
    )

    output.centered(options.as_row(inter_indentation=output.column_percentual_indentation(0.08)), '\n')

    selection = prompt_relentlessly('', indentation_percentage=0.49, options=list(options))

    if authentication_result := options[selection].__call__():
        return authentication_result
    return __call__()
