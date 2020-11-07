from typing import Dict, Any, Union, Type
import random

from backend import language_metadata

from frontend.state import State
from frontend.reentrypoint import ReentryPoint, ReentryPointProvider
from frontend.utils import query, output, view, date
from frontend.trainers import (
    SentenceTranslationTrainerFrontend,
    VocableTrainerFrontend,
    VocableAdderFrontend
)
from frontend.screen.ops import INTER_OPTION_INDENTATION


ActionOption = Union[
    Type[SentenceTranslationTrainerFrontend],
    Type[VocableTrainerFrontend],
    Type[VocableAdderFrontend],
    ReentryPointProvider
]


KEYWORD_2_ACTION: Dict[str, ActionOption] = {
    'sentence': SentenceTranslationTrainerFrontend,
    'vocabulary': VocableTrainerFrontend,
    'add': VocableAdderFrontend,
    'home': lambda: ReentryPoint.Home,
    'quit': lambda: ReentryPoint.Exit
}


@view.view_creator(banner='lingularity/3d-ascii', banner_color='green')
def __call__(is_new_user=False) -> ReentryPoint:
    view.set_terminal_title(f'{State.language} Training Selection')

    # display welcome message in case of new user
    if is_new_user:
        _display_welcome_message(username=State.username)

    _display_constitution_query(username=State.username, language=State.language)

    # query desired action
    action_selection: ActionOption = _query_action_selection()

    # instantiate frontend if selected
    callable_action: ReentryPointProvider
    if isinstance(action_selection, type):
        callable_action = action_selection()
    else:
        callable_action = action_selection

    return callable_action()


def _display_welcome_message(username: str):
    output.centered_print(f"Fancy seeing you here, {username}", '\n' * 2)


def _display_constitution_query(username: str, language: str):
    if constitution_query_templates := language_metadata[language]['translations'].get('constitutionQuery'):
        constitution_queries = map(lambda query: query.replace('{}', username), constitution_query_templates)
    else:
        constitution_queries = map(lambda query: query + f' {username}?', [f"What's up", f"How are you"])

    output.centered_print(random.choice(list(constitution_queries)), '\n' * 2)


def _display_last_session_conclusion(last_session_metrics: Dict[str, Any]):
    output.centered_print(f"You faced {last_session_metrics['nFacedItems']} "
                          f"{['sentences', 'vocables'][last_session_metrics['trainer'] == 'v']} "
                          f"during your last session {date.date_repr(last_session_metrics['date'])}", '\n' * 3)


def _query_action_selection() -> ActionOption:
    output.centered_print(f"What would you like to do?: "
                          f"{INTER_OPTION_INDENTATION}Translate (S)entences"
                          f"{INTER_OPTION_INDENTATION}Train (V)ocabulary"
                          f"{INTER_OPTION_INDENTATION}(A)dd Vocabulary"
                          f"{INTER_OPTION_INDENTATION}Return to (H)ome Screen"
                          f"{INTER_OPTION_INDENTATION}(Q)uit")

    action_selection_keyword = query.relentlessly(
        query_message=output.centered_print_indentation(' '),
        options=list(KEYWORD_2_ACTION.keys())
    )
    return KEYWORD_2_ACTION[action_selection_keyword]
