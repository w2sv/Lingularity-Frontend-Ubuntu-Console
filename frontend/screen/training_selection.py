from typing import Dict, Any, Union, Type, Optional, List
import random

from backend import language_metadata

from frontend import asciichartpy
from frontend.state import State
from frontend.reentrypoint import ReentryPoint
from frontend.utils import query, output, view, date
from frontend.trainers import (
    SentenceTranslationTrainerFrontend,
    VocableTrainerFrontend,
    VocableAdderFrontend,
    TrainerFrontend
)
from .ops import INTER_OPTION_INDENTATION


_ActionOption = Union[
    Type[SentenceTranslationTrainerFrontend],
    Type[VocableTrainerFrontend],
    Type[VocableAdderFrontend],
    ReentryPoint
]


_KEYWORD_2_ACTION: Dict[str, _ActionOption] = {
    'sentence': SentenceTranslationTrainerFrontend,
    'vocabulary': VocableTrainerFrontend,
    'add': VocableAdderFrontend,
    'home': ReentryPoint.Home,
    'quit': ReentryPoint.Exit
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
    if (action_selection_keyword := _query_action_selection()) == query.CANCELLED:
        return ReentryPoint.Home
    action_selection = _KEYWORD_2_ACTION[action_selection_keyword]

    # instantiate frontend if selected
    if _is_trainer_frontend(action_selection):
        trainer_frontend = action_selection()
        return __call__(training_item_sequence=trainer_frontend.__call__())  # type: ignore

    return action_selection  # type: ignore


def _query_action_selection() -> str:
    output.centered(f"{INTER_OPTION_INDENTATION}Translate (S)entences"
                    f"{INTER_OPTION_INDENTATION}Train (V)ocabulary"
                    f"{INTER_OPTION_INDENTATION}(A)dd Vocabulary"
                    f"{INTER_OPTION_INDENTATION}Return to (H)ome Screen"
                    f"{INTER_OPTION_INDENTATION}(Q)uit", '\n')

    return query.relentlessly(
        prompt=output.centering_indentation(' '),
        options=list(_KEYWORD_2_ACTION.keys()),
        cancelable=True
    )


def _is_trainer_frontend(action: _ActionOption) -> bool:
    return isinstance(action, type) and issubclass(action, TrainerFrontend)


def _display_constitution_query(username: str, language: str):
    if constitution_query_templates := language_metadata[language]['translations'].get('constitutionQuery'):
        constitution_queries = map(lambda query: query.replace('{}', username), constitution_query_templates)
    else:
        constitution_queries = map(lambda query: query + f' {username}?', [f"What's up", f"How are you"])

    output.centered(random.choice(list(constitution_queries)), view.VERTICAL_OFFSET)


def _display_training_item_sequence(training_item_sequence: List[int]):
    chart = asciichartpy.plot(training_item_sequence, config=asciichartpy.Config(  # type: ignore
        height=15,
        horizontal_point_spacing=5,
        offset=30,
        format='{:8.0f}',
        colors=[asciichartpy.colors.RED],
        display_x_axis=True
    ))

    print(chart, view.VERTICAL_OFFSET)


def _display_last_session_conclusion(last_session_metrics: Dict[str, Any]):
    output.centered(f"You faced {last_session_metrics['nFacedItems']} "
                    f"{['sentences', 'vocables'][last_session_metrics['trainer'] == 'v']} "
                    f"during your last session {date.date_repr(last_session_metrics['date'])}", '\n' * 3)
