import random
from typing import Optional, Type, Union

import asciiplot
from backend.src.metadata import language_metadata

from frontend.src.reentrypoint import ReentryPoint
from frontend.src.screen.action_option import Option, Options
from frontend.src.state import State
from frontend.src.trainers import (SentenceTranslationTrainerFrontend, TrainerFrontend, VocableAdderFrontend, VocableTrainerFrontend)
from frontend.src.trainers.base.sequence_plot_data import SequencePlotData
from frontend.src.utils import output, view
from frontend.src.utils.query.cancelling import QUERY_CANCELLED
from frontend.src.utils.query.repetition import query_relentlessly
from frontend.src.utils.view import terminal


_options = Options([
    Option('Translate Sentences', keyword_index=1, callback=SentenceTranslationTrainerFrontend),
    Option('Train Vocabulary', keyword_index=1, callback=VocableTrainerFrontend),
    Option('Add Vocabulary', keyword_index=0, callback=VocableAdderFrontend),
    Option('Quit', callback=ReentryPoint.Exit)
])


@view.creator(banner_args=('lingularity/3d-ascii', 'green'))
@State.receiver
def __call__(state: State, training_item_sequence_plot_data: Optional[SequencePlotData] = None) -> ReentryPoint:
    terminal.set_title(f'{state.language} Training Selection')

    if not training_item_sequence_plot_data:
        _display_constitution_query(username=state.username, language=state.language)

    # display training item sequences corresponding to previous training action
    else:
        _display_training_item_sequence(training_item_sequence_plot_data)

    # query desired action
    if (action_selection_keyword := _query_action_selection()) == QUERY_CANCELLED:
        return ReentryPoint.Home
    option_callback = _options[action_selection_keyword]

    # instantiate frontend if selected
    if _is_trainer_frontend(option_callback):
        trainer_frontend = option_callback()
        return __call__(training_item_sequence_plot_data=trainer_frontend.__call__())

    return option_callback


def _query_action_selection() -> str:
    output.centered(_options.display_row, '\n')
    return query_relentlessly(prompt=output.centering_indentation(' '), options=_options.keywords, cancelable=True)


_OptionCallbacks = Union[
    Type[SentenceTranslationTrainerFrontend],
    Type[VocableTrainerFrontend],
    Type[VocableAdderFrontend],
    ReentryPoint
]


def _is_trainer_frontend(action: _OptionCallbacks) -> bool:
    return isinstance(action, type) and issubclass(action, TrainerFrontend)


def _display_constitution_query(username: str, language: str):
    if constitution_query_templates := language_metadata[language]['translations'].get('constitutionQuery'):
        constitution_queries = map(lambda query_corpus: query_corpus.replace('{}', username), constitution_query_templates)
    else:
        constitution_queries = map(lambda query_corpus: query_corpus + f' {username}?', [f"What's up", f"How are you"])

    output.centered(random.choice(list(constitution_queries)), view.VERTICAL_OFFSET)


def _display_training_item_sequence(training_item_sequence_plot_data: SequencePlotData):
    y_label_max_length = max(map(lambda label: len(str(label)), training_item_sequence_plot_data.sequence))
    outer_left_x_label = 'two weeks ago'
    color = [asciiplot.Color.BLUE, asciiplot.Color.RED][training_item_sequence_plot_data.item_name.startswith(
        's')]

    try:
        chart = asciiplot.asciiize(
            training_item_sequence_plot_data.sequence,
            height=15,
            inter_points_margin=5,
            indentation=max(len(outer_left_x_label) // 2 - y_label_max_length, 0),
            y_ticks_decimal_places=0,
            sequence_colors=[color],
            axis_description_color=color,
            label_color=asciiplot.Color.MAGENTA,
            x_ticks={0: outer_left_x_label, 14: 'today'},
            x_axis_description='date',
            y_axis_description=training_item_sequence_plot_data.item_name
        )
        output.centered(chart, view.VERTICAL_OFFSET)

    except ZeroDivisionError:
        pass
