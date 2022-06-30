from typing import Dict
import itertools

from backend.src.database import UserMongoDBClient
from backend.src.string_resources import string_resources
from termcolor import colored

from frontend.src.metadata import main_country_flag
from frontend.src.utils import query, output
from frontend.src.utils import view
from frontend.src.state import State
from frontend.src.reentrypoint import ReentryPoint, ReentryPointProvider
from frontend.src.screen import action_option, account_deletion
from frontend.src.utils.query.cancelling import QUERY_CANCELLED
from frontend.src.utils.query._ops import indicate_erroneous_input
from frontend.src.utils.query.repetition import query_relentlessly
from frontend.src.utils.view import terminal


@view.creator(title=terminal.DEFAULT_TERMINAL_TITLE, banner_args=('lingularity/ansi-shadow', 'red'))
@State.receiver
def __call__(state: State) -> ReentryPoint:
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
    for language_group in output.group_by_starting_letter(state.user_languages, is_sorted=False):
        output.centered('  '.join(map(lambda language: f'{language} {main_country_flag(language)}', language_group)))

    # display option descriptions
    DESCRIPTIONS = ['Add Language', 'Remove Language', 'Sign Out', 'Delete Account', 'Quit']
    descriptions = list(
        map(
            lambda description: action_option.color_description(description, keyword_index=0, color='red'),
            DESCRIPTIONS
        )
    )

    OPTION_CLASS_DELIMITER = colorized_header('   |   ')

    OPTION_BLOCK = (
        f"{colorized_header('ADDITIONAL OPTIONS:')}{action_option.OFFSET}{descriptions[0]}{action_option.OFFSET}"
        f"{descriptions[1]}"
        f"{OPTION_CLASS_DELIMITER}{descriptions[2]}{action_option.OFFSET}{descriptions[3]}"
        f"{OPTION_CLASS_DELIMITER}{descriptions[4]}"
    )
    output.centered(f'\n{OPTION_BLOCK}\n')

    # query language/options selection
    selection = query_relentlessly(
        prompt='Select Language/Option: ', indentation_percentage=0.35,
        options=list(state.user_languages) + _OPTION_KEYWORDS
    )

    # exit and reenter at respective reentry point in case of option selection
    if reentry_point := _OPTION_2_REENTRY_POINT.get(selection):
        return reentry_point

    elif reentry_point_provider := _OPTION_2_REENTRY_POINT_PROVIDER.get(selection):
        return reentry_point_provider()

    # query reference language in case of English being selected
    if train_english := selection == string_resources['english']:
        mongodb_client = UserMongoDBClient.instance()

        selection = mongodb_client.query_reference_language()
        mongodb_client.set_reference_language(reference_language=selection)

    # write selected language into state
    state.set_language(non_english_language=selection, train_english=train_english)

    return ReentryPoint.TrainingSelection


@State.receiver
def _language_removal(state: State) -> ReentryPoint:
    """ Queries language whose user wishes to erase from his profile with confirmation query,
        thereupon removes language from user languages stored in State, respective user data
        from database if applicable

        Invokes home screen afterwards """

    # erase everything until before option row
    output.erase_lines(3)
    output.empty_row(2)

    # exit in case of nonexistence of removable languages
    if not len(state.user_languages):
        indicate_erroneous_input('THERE ARE NO LANGUAGES TO BE REMOVED', sleep_duration=1.5)
        return __call__()

    # query removal language
    if (removal_language := query_relentlessly(
            'Enter language you wish to remove: ', indentation_percentage=0.3,
            options=list(state.user_languages), cancelable=True
    )) == QUERY_CANCELLED:
        return __call__()

    output.erase_lines(1)

    # query confirmation, remove language from user languages stored in State,
    # respective user data from database
    output.centered(
        f'Are you sure you want to irretrievably erase all {removal_language} user data? {query.YES_NO_QUERY_OUTPUT}'
    )
    if query_relentlessly('', indentation_percentage=0.5, options=query.YES_NO_OPTIONS) == 'yes':
        UserMongoDBClient.instance().remove_language_data(removal_language)
        state.user_languages.remove(removal_language)

    return __call__()