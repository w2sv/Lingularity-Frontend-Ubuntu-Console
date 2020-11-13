from typing import Dict
import itertools

from backend import string_resources
from backend import MongoDBClient
from termcolor import colored

from frontend.utils import query, output, view
from frontend.state import State
from frontend.reentrypoint import ReentryPoint, ReentryPointProvider
from frontend.screen import account_deletion, ops


@view.creator(title='Acquire Languages the Litboy Way', banner='lingularity/ansi-shadow', banner_color='red')
def __call__() -> ReentryPoint:
    """ Displays languages already used by user, as well as additional procedure options of
            - adding a new language
            - signing into another account
            - terminating the program

        Thereupon queries desired training language/option.
        Selected language will be written into global state if applicable.

        Returns:
            in case of option selection ReentryPoint corresponding to the selected one,
                all of which are denoted in _OPTION_2_REENTRY_POINT and _OPTION_2_REENTRY_POINT_PROVIDER,
                ReentryPoint.TrainingSelection in case of language selection """

    _OPTION_2_REENTRY_POINT: Dict[str, ReentryPoint] = {
        'add language': ReentryPoint.LanguageAddition,
        'sign out': ReentryPoint.Login,
        'quit': ReentryPoint.Exit,
    }

    _OPTION_2_REENTRY_POINT_PROVIDER: Dict[str, ReentryPointProvider] = {
        'remove language': _language_removal,
        'delete account': account_deletion.__call__
    }

    _OPTION_KEYWORDS = list(itertools.chain(_OPTION_2_REENTRY_POINT.keys(), _OPTION_2_REENTRY_POINT_PROVIDER.keys()))

    def colorized_header(header: str) -> str:
        return colored(header, 'blue')

    # display languages already used by user
    output.centered(colorized_header('YOUR LANGUAGES'), "\n")
    for language_group in output.group_by_starting_letter(State.user_languages, is_sorted=False):
        output.centered('  '.join(language_group))

    # display options
    DELIMITER = colorized_header('   |   ')
    OPTION_BLOCK = (
        f"{colorized_header('ADDITIONAL OPTIONS:')}{ops.INTER_OPTION_INDENTATION}(A)dd Language{ops.INTER_OPTION_INDENTATION}(R)emove Language"
        f"{DELIMITER}(S)ign Out{ops.INTER_OPTION_INDENTATION}(D)elete Account"
        f"{DELIMITER}(Q)uit"
    )

    output.centered(f'\n{OPTION_BLOCK}\n')

    # query language/options selection
    selection = query.relentlessly(prompt='Select Language/Option: ',
                                   options=list(State.user_languages) + _OPTION_KEYWORDS,
                                   indentation_percentage=0.35)

    # exit and reenter at respective reentry point in case of option selection
    if reentry_point := _OPTION_2_REENTRY_POINT.get(selection):
        return reentry_point

    elif reentry_point_provider := _OPTION_2_REENTRY_POINT_PROVIDER.get(selection):
        return reentry_point_provider()

    # query reference language in case of English being selected
    train_english = False
    if selection == string_resources.ENGLISH:
        train_english = True
        selection = ops.reference_language.query_database()

    # write selected language into state
    State.set_language(non_english_language=selection, train_english=train_english)

    return ReentryPoint.TrainingSelection


def _language_removal() -> ReentryPoint:
    """ Queries language whose user wishes to erase from his profile with confirmation query,
        thereupon removes language from user languages stored in State, respective user data
        from database if applicable

        Invokes home screen afterwards """

    # erase everything until before option row
    output.erase_lines(3)

    # exit in case of nonexistence of removable languages
    if not len(State.user_languages):
        query.indicate_erroneous_input('THERE ARE NO LANGUAGES TO BE REMOVED', sleep_duration=1.5)
        return __call__()

    # query removal language
    removal_language = query.relentlessly(
        'Enter language you wish to remove: ',
        options=list(State.user_languages),
        indentation_percentage=0.3
    )

    output.erase_lines(1)

    # query confirmation, remove language from user languages stored in State,
    # respective user data from database
    output.centered(f'Are you sure you want to irretrievably erase all {removal_language} user data? {query.YES_NO_QUERY_OUTPUT}')
    if query.relentlessly('', options=query.YES_NO_OPTIONS, indentation_percentage=0.5) == 'yes':
        MongoDBClient.get_instance().remove_language_data(removal_language)
        State.user_languages.remove(removal_language)

    return __call__()
