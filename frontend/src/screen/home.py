from backend.src.database.user_database import UserDatabase
from backend.src.string_resources import string_resources
from termcolor import colored

from frontend.src import option
from frontend.src.option import Option, OptionCollection
from frontend.src.reentrypoint import ReentryPoint
from frontend.src.screen import account_deletion
from frontend.src.state import State
from frontend.src.utils import output, prompt, view
from frontend.src.utils.prompt._ops import indicate_erroneous_input
from frontend.src.utils.prompt.cancelling import QUERY_CANCELLED
from frontend.src.utils.prompt.repetition import prompt_relentlessly
from frontend.src.utils.view import Banner, terminal


@view.creator(title=terminal.DEFAULT_TERMINAL_TITLE, banner=Banner('lingularity/ansi-shadow', 'red'))
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

    options = OptionCollection(
        [
            Option('Add language', ReentryPoint.LanguageAddition),
            Option('Remove language', _language_removal),

            Option('Sign Out', ReentryPoint.Login),
            Option('Delete Account', account_deletion.__call__),

            Option('Quit', ReentryPoint.Exit)
        ]
    )

    _render_screen(options)
    return _proceed(options)


@State.receiver
def _render_screen(options: OptionCollection, state: State):
    _colored = lambda header: colored(header, 'blue')

    # display languages already used by user
    output.centered(_colored('YOUR LANGUAGES'), "\n")
    for language in state.user_languages:
        output.centered(language)

    option_delimiter = _colored('   |   ')

    OPTION_BLOCK = (
        f"{_colored('OPTIONS:')}{option.OFFSET}{options.formatted_descriptions[0]}{option.OFFSET}"
        f"{options.formatted_descriptions[1]}"
        f"{option_delimiter}{options.formatted_descriptions[2]}{option.OFFSET}{options.formatted_descriptions[3]}"
        f"{option_delimiter}{options.formatted_descriptions[4]}"
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
        user_database: UserDatabase = UserDatabase.instance()

        selection = user_database.language_metadata_collection.query_reference_language()
        user_database.language_metadata_collection.set_reference_language(reference_language=selection)

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
        UserDatabase.instance().remove_language_related_documents()
        state.user_languages.remove(removal_language)

    return __call__()