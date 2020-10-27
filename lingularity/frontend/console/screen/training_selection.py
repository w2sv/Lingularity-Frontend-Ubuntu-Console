from typing import Dict, Any, Union, Callable, Type
import random

from lingularity.backend.metadata import language_metadata

from . import ops
from lingularity.frontend.console.state import State
from lingularity.frontend.console.reentrypoint import ReentryPoint
from lingularity.frontend.console.utils import view, output, date, input_resolution
from lingularity.frontend.console.trainers import (
    SentenceTranslationTrainerConsoleFrontend,
    VocableTrainerConsoleFrontend,
    VocableAdderFrontend,
    TrainerConsoleFrontend
)


Action = Union[Type[TrainerConsoleFrontend], Callable]


KEYWORD_2_ACTION: Dict[str, Action] = {
    'sentence': SentenceTranslationTrainerConsoleFrontend,
    'vocabulary': VocableTrainerConsoleFrontend,
    'add': VocableAdderFrontend,
    'home': lambda: ReentryPoint.LanguageSelection
}


@view.view_creator(banner_kind='3d-ascii', banner_color='green')
def __call__(is_new_user=False) -> ReentryPoint:
    view.set_terminal_title(f'{State.language} Training Selection')

    if is_new_user:
        _display_welcome_message(username=State.username)

    _display_constitution_query(State.username, language=State.language)

    action_selection = _select_action()

    if isinstance(action_selection, type):
        action_selection = action_selection()

    return action_selection.__call__()  # type: ignore


def _display_welcome_message(username: str):
    output.centered_print(f"Fancy seeing you here, {username}.\n\n")


def _display_constitution_query(username: str, language: str):
    if constitution_query_templates := language_metadata[language]['translations'].get('constitutionQuery'):
        constitution_queries = map(lambda query: query.replace('{}', username), constitution_query_templates)
    else:
        constitution_queries = map(lambda query: query + f' {username}?', [f"What's up", f"How are you"])

    output.centered_print(random.choice(list(constitution_queries)), '\n' * 2)


def _display_last_session_conclusion(last_session_metrics: Dict[str, Any]):
    output.centered_print(f"You faced {last_session_metrics['nFacedItems']} {['sentences', 'vocables'][last_session_metrics['trainer'] == 'v']} during your last session {date.date_repr(last_session_metrics['date'])}\n\n\n")


def _select_action() -> Action:
    output.centered_print(f"What would you like to do?: "
                          f"{output.INTER_OPTION_INDENTATION}Translate (S)entences"
                          f"{output.INTER_OPTION_INDENTATION}Train (V)ocabulary"
                          f"{output.INTER_OPTION_INDENTATION}(A)dd Vocabulary"
                          f"{output.INTER_OPTION_INDENTATION}Go back to (H)ome Screen")

    action_selection_keyword = input_resolution.query_relentlessly(query_message=output.centered_print_indentation(' '), options=list(KEYWORD_2_ACTION.keys()))
    return KEYWORD_2_ACTION[action_selection_keyword]
