from typing import Optional

from backend import string_resources

from frontend.utils import query, output, view
from frontend.state import State
from frontend.reentrypoint import ReentryPoint
from frontend.screen.ops import INTER_OPTION_INDENTATION, reference_language


_OPTION_2_REENTRY_POINT = {
        'add': ReentryPoint.LanguageAddition,
        'sign': ReentryPoint.Login,
        'quit': ReentryPoint.Exit
    }

_OPTION_KEYWORDS = list(_OPTION_2_REENTRY_POINT.keys())


@view.view_creator(title='Acquire Languages the Litboy Way', banner='lingularity/ansi-shadow', banner_color='red')
def __call__() -> Optional[ReentryPoint]:
    """ Displays languages already used by user, as well as additional procedure options of
            - adding a new language
            - signing into another account
            - terminating the program

        Thereupon queries desired training language/option.

        Returns:
            None in case of language selection, in which the aforementioned
                will also be written into the global state
            ReentryPoint corresponding to the selected option, denoted in
                _OPTION_2_REENTRY_POINT """

    # display languages already used by user
    output.centered_print("YOUR LANGUAGES:\n")
    for language_group in output.group_by_starting_letter(State.user_languages, is_sorted=False):
        output.centered_print('  '.join(language_group))

    # display options
    output.centered_print(f"\nAdditional Options: "
                          f"{INTER_OPTION_INDENTATION}(A)dd Language"
                          f"{INTER_OPTION_INDENTATION}(S)ign Out"
                          f"{INTER_OPTION_INDENTATION}(Q)uit\n")

    # query language/options selection
    selection = query.relentlessly(query_message='Select Language/Option: ', options=list(State.user_languages) + _OPTION_KEYWORDS)

    # exit and reenter at respective reentry point in case of option selection
    if selection in _OPTION_KEYWORDS:
        return _OPTION_2_REENTRY_POINT[selection]

    # query reference language in case of English being selected
    train_english = False
    if selection == string_resources.ENGLISH:
        train_english = True
        selection = reference_language.query_database()

    # write selected language into state
    State.set_language(non_english_language=selection, train_english=train_english)

    return None
