from backend.src.database import UserMongoDBClient
from backend.src.string_resources import string_resources
from termcolor import colored

from frontend.src.metadata import main_country_flag
from frontend.src.reentrypoint import ReentryPoint
from frontend.src.screen import account_deletion
from frontend.src import option
from frontend.src.option import Option, OptionCollection
from frontend.src.state import State
from frontend.src.utils import output, prompt, view
from frontend.src.utils.prompt._ops import indicate_erroneous_input
from frontend.src.utils.prompt.cancelling import QUERY_CANCELLED
from frontend.src.utils.prompt.repetition import prompt_relentlessly
from frontend.src.utils.view import Banner, terminal


@view.creator(title=terminal.DEFAULT_TERMINAL_TITLE, banner=Banner('lingularity/ansi-shadow', 'red'))
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

    options = OptionCollection(
        [
            Option('add', 'Add language', ReentryPoint.LanguageAddition),
            Option('sign', 'Sign Out', ReentryPoint.Login),
            Option('quit', 'Quit', ReentryPoint.Exit),

            Option('remove', 'Remove language', _language_removal),
            Option('delete', 'Delete Account', account_deletion.__call__)
        ]
    )

    _render_screen(options)
    return _proceed(options)


@State.receiver
def _render_screen(options: OptionCollection, state: State):
    _colored = lambda header: colored(header, 'blue')

    # display languages already used by user
    output.centered(_colored('YOUR LANGUAGES'), "\n")
    for language_group in output.group_by_starting_letter(state.user_languages, is_sorted=False):
        output.centered('  '.join(map(lambda language: f'{language} {main_country_flag(language)}', language_group)))

    OPTION_CLASS_DELIMITER = _colored('   |   ')

    OPTION_BLOCK = (
        f"{_colored('ADDITIONAL OPTIONS:')}{option.OFFSET}{options.formatted_descriptions[0]}{option.OFFSET}"
        f"{options.formatted_descriptions[1]}"
        f"{OPTION_CLASS_DELIMITER}{options.formatted_descriptions[2]}{option.OFFSET}{options.formatted_descriptions[3]}"
        f"{OPTION_CLASS_DELIMITER}{options.formatted_descriptions[4]}"
    )
    output.centered(f'\n{OPTION_BLOCK}\n')


@State.receiver
def _proceed(options: OptionCollection, state: State) -> ReentryPoint:
    selection = prompt_relentlessly(
        prompt='Select Language/Option: ',
        indentation_percentage=0.35,
        options=list(state.user_languages) + list(options)
    )

    if (callback := options.get(selection)) is not None:
        if isinstance(callback, ReentryPoint):
            return callback
        return callback()

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
    if (removal_language := prompt_relentlessly(
            'Enter language you wish to remove: ',
            indentation_percentage=0.3,
            options=list(state.user_languages),
            cancelable=True
    )) == QUERY_CANCELLED:
        return __call__()

    output.erase_lines(1)

    # query confirmation, remove language from user languages stored in State,
    # respective user data from database
    output.centered(
        f'Are you sure you want to irretrievably erase all {removal_language} user data? {prompt.YES_NO_QUERY_OUTPUT}'
    )
    if prompt_relentlessly('', indentation_percentage=0.5, options=prompt.YES_NO_OPTIONS) == 'yes':
        UserMongoDBClient.instance().remove_language_data(removal_language)
        state.user_languages.remove(removal_language)

    return __call__()