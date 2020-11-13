from typing import Dict, Any, Union, Type, Optional, List
import random

from backend import language_metadata

from frontend import asciichartpy
from frontend.state import State
from frontend.reentrypoint import ReentryPoint, ReentryPointProvider
from frontend.utils import query, output, view, date
from frontend.trainers import (
    SentenceTranslationTrainerFrontend,
    VocableTrainerFrontend,
    VocableAdderFrontend,
    TrainerFrontend
)
from .ops import INTER_OPTION_INDENTATION


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


@view.creator(banner='lingularity/3d-ascii', banner_color='green')
def __call__(training_item_sequence: Optional[List[int]] = None) -> ReentryPoint:
    view.set_terminal_title(f'{State.language} Training Selection')

    if training_item_sequence is None:
        _display_constitution_query(username=State.username, language=State.language)

    # display training item sequences corresponding to previous training action
    else:
        _display_training_item_sequence(training_item_sequence)

    # query desired action
    action_selection: ActionOption = _query_action_selection()

    # instantiate frontend if selected
    if _is_trainer_frontend(action_selection):
        trainer_frontend = action_selection()
        return __call__(training_item_sequence=trainer_frontend.__call__())  # type: ignore

    return action_selection()  # type: ignore


def _query_action_selection() -> ActionOption:
    output.centered(f"{INTER_OPTION_INDENTATION}Translate (S)entences"
                    f"{INTER_OPTION_INDENTATION}Train (V)ocabulary"
                    f"{INTER_OPTION_INDENTATION}(A)dd Vocabulary"
                    f"{INTER_OPTION_INDENTATION}Return to (H)ome Screen"
                    f"{INTER_OPTION_INDENTATION}(Q)uit", '\n')

    action_selection_keyword = query.relentlessly(
        prompt=output.centering_indentation(' '),
        options=list(KEYWORD_2_ACTION.keys())
    )
    return KEYWORD_2_ACTION[action_selection_keyword]


def _is_trainer_frontend(action: ActionOption) -> bool:
    return isinstance(action, type) and issubclass(action, TrainerFrontend)


def _display_constitution_query(username: str, language: str):
    if constitution_query_templates := language_metadata[language]['translations'].get('constitutionQuery'):
        constitution_queries = map(lambda query: query.replace('{}', username), constitution_query_templates)
    else:
        constitution_queries = map(lambda query: query + f' {username}?', [f"What's up", f"How are you"])

    output.centered(random.choice(list(constitution_queries)), '\n' * 2)


def _display_training_item_sequence(training_item_sequence: List[int]):
    chart = asciichartpy.plot(training_item_sequence, config=asciichartpy.Config(  # type: ignore
        height=15,
        horizontal_point_spacing=5,
        offset=30,
        format='{:8.0f}',
        colors=[asciichartpy.colors.RED],
        display_x_axis=True
    ))

    print(chart, '\n' * 2)


def _display_last_session_conclusion(last_session_metrics: Dict[str, Any]):
    output.centered(f"You faced {last_session_metrics['nFacedItems']} "
                    f"{['sentences', 'vocables'][last_session_metrics['trainer'] == 'v']} "
                    f"during your last session {date.date_repr(last_session_metrics['date'])}", '\n' * 3)
