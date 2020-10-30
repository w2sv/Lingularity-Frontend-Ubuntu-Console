from typing import Optional

from lingularity.backend.utils import string_resources

from .ops import INTER_OPTION_INDENTATION, reference_language
from lingularity.frontend.utils import input_resolution, output, view
from lingularity.frontend.state import State
from lingularity.frontend.reentrypoint import ReentryPoint


_OPTION_2_REENTRY_POINT = {
        'add': ReentryPoint.LanguageAddition,
        'sign': ReentryPoint.Login,
        'quit': ReentryPoint.Exit
    }

_OPTION_KEYWORDS = list(_OPTION_2_REENTRY_POINT.keys())


@view.view_creator(title='Acquire Languages the Litboy Way', banner='lingularity/ansi-shadow', banner_color='red')
def __call__() -> Optional[ReentryPoint]:
    """ Returns:
            return_to_language_addition_flag: bool """

    train_english = False

    output.centered_print("YOUR LANGUAGES:\n")
    for language_group in output.group_by_starting_letter(State.user_languages, is_sorted=False):
        output.centered_print('  '.join(language_group))

    output.centered_print(f"\nAdditional Options: "
                          f"{INTER_OPTION_INDENTATION}(A)dd Language"
                          f"{INTER_OPTION_INDENTATION}(S)ign Out"
                          f"{INTER_OPTION_INDENTATION}(Q)uit\n")

    selection = input_resolution.query_relentlessly(query_message='Select Language/Option: ', options=list(State.user_languages) + _OPTION_KEYWORDS)

    if selection in _OPTION_KEYWORDS:
        return _OPTION_2_REENTRY_POINT[selection]

    if selection == string_resources.ENGLISH:
        train_english = True
        selection = reference_language.query()

    State.set_language(non_english_language=selection, train_english=train_english)

    return None
