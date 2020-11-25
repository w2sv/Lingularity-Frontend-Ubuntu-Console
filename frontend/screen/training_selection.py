from typing import Dict, Any, Union, Type, Optional
import random

from backend import language_metadata
import asciichartpy_extended

from frontend.state import State
from frontend.reentrypoint import ReentryPoint
from frontend.utils import query, output, view, date
from frontend.trainers import (
    SentenceTranslationTrainerFrontend,
    VocableTrainerFrontend,
    VocableAdderFrontend,
    TrainerFrontend
)
from frontend.trainers.base.sequence_plot_data import SequencePlotData
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
    'quit': ReentryPoint.Exit
}


@view.creator(banner='lingularity/3d-ascii', banner_color='green')
def __call__(training_item_sequence_plot_data: Optional[SequencePlotData] = None) -> ReentryPoint:
    view.set_terminal_title(f'{State.language} Training Selection')

    if not training_item_sequence_plot_data:
        _display_constitution_query(username=State.username, language=State.language)

    # display training item sequences corresponding to previous training action
    else:
        _display_training_item_sequence(training_item_sequence_plot_data)

    # query desired action
    if (action_selection_keyword := _query_action_selection()) == query.CANCELLED:
        return ReentryPoint.Home
    action_selection = _KEYWORD_2_ACTION[action_selection_keyword]

    # instantiate frontend if selected
    if _is_trainer_frontend(action_selection):
        trainer_frontend = action_selection()  # type: ignore
        return __call__(training_item_sequence_plot_data=trainer_frontend.__call__())

    return action_selection  # type: ignore


def _query_action_selection() -> str:
    output.centered(f"{INTER_OPTION_INDENTATION}Translate (S)entences"
                    f"{INTER_OPTION_INDENTATION}Train (V)ocabulary"
                    f"{INTER_OPTION_INDENTATION}(A)dd Vocabulary"
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


def _display_training_item_sequence(training_item_sequence_plot_data: SequencePlotData):
    y_label_max_length = max(map(lambda label: len(str(label)), training_item_sequence_plot_data.sequence))
    outer_left_x_label = 'two weeks ago'
    color = [asciichartpy_extended.colors.BLUE, asciichartpy_extended.colors.RED][training_item_sequence_plot_data.item_name.startswith('s')]

    try:
        chart = asciichartpy_extended.asciiize(training_item_sequence_plot_data.sequence, config=asciichartpy_extended.Config(
            plot_height=15,
            columns_between_points=5,
            label_column_offset=max(len(outer_left_x_label) // 2 - y_label_max_length, 0),
            y_label_decimal_places=0,
            sequence_colors=[color],
            axis_description_color=color,
            x_axis_label_color=asciichartpy_extended.colors.MAGENTA,
            display_x_axis=True,
            x_labels={0: outer_left_x_label, 14: 'today'},
            x_axis_description='date',
            y_axis_description=training_item_sequence_plot_data.item_name
        ))
        output.centered(chart, view.VERTICAL_OFFSET)

    except ZeroDivisionError:
        pass


def _display_last_session_conclusion(last_session_metrics: Dict[str, Any]):
    output.centered(f"You faced {last_session_metrics['nFacedItems']} "
                    f"{['sentences', 'vocables'][last_session_metrics['trainer'] == 'v']} "
                    f"during your last session {date.date_repr(last_session_metrics['date'])}", '\n' * 3)
