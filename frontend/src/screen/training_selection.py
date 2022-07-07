from __future__ import annotations

import random

import asciiplot
from backend.src.database.user_database import UserDatabase
from backend.src.metadata import language_metadata

from frontend.src.reentrypoint import ReentryPoint
from frontend.src.option import Option, OptionCollection
from frontend.src.state import State
from frontend.src.trainer_frontends.sentence_translation import SentenceTranslationTrainerFrontend
from frontend.src.sequence_plot_data import SequencePlotData
from frontend.src.trainer_frontends.trainer_frontend import TrainerFrontend
from frontend.src.trainer_frontends.vocable_adder import VocableAdderFrontend
from frontend.src.trainer_frontends.vocable_trainer import VocableTrainerFrontend
from frontend.src.utils import output, view
from frontend.src.utils.prompt.cancelling import QUERY_CANCELLED
from frontend.src.utils.prompt.repetition import prompt_relentlessly
from frontend.src.utils.view import Banner


@view.creator(banner=Banner('lingularity/3d-ascii', 'green'), title='Training Selection')
def __call__(training_item_sequence_plot_data: SequencePlotData | None = None) -> ReentryPoint:
    _render_screen(training_item_sequence_plot_data)

    options = _get_options()

    # query desired action
    if (action_selection_keyword := _query_action_selection(options)) == QUERY_CANCELLED:
        return ReentryPoint.Home

    callback = options[action_selection_keyword]

    # instantiate frontend if selected
    if isinstance(callback, ReentryPoint):
        return callback
    assert issubclass(callback, TrainerFrontend)
    trainer_frontend = callback()
    return __call__(training_item_sequence_plot_data=trainer_frontend())


@UserDatabase.receiver
def _get_options(user_database: UserDatabase) -> OptionCollection:
    options = [Option('Translate Sentences', callback=SentenceTranslationTrainerFrontend, keyword='sentences')]

    if user_database.language in user_database.vocabulary_collection.vocabulary_possessing_languages():
        options.append(Option('Train Vocabulary', callback=VocableTrainerFrontend, keyword='vocabulary'))

    options.append(Option('Add Vocabulary', callback=VocableAdderFrontend))
    options.append(Option('Home Screen', callback=ReentryPoint.Home))

    return OptionCollection(options)


def _query_action_selection(options: OptionCollection) -> str:
    output.centered(options.as_row(), '\n')
    return prompt_relentlessly(
        prompt=output.centering_indentation(' '),
        options=list(options),
        cancelable=True
    )


@State.receiver
def _render_screen(training_item_sequence_plot_data: SequencePlotData | None, state: State):
    if training_item_sequence_plot_data:
        _display_training_item_sequence(training_item_sequence_plot_data)
    else:
        _display_constitution_query(username=state.username, language=state.language)


def _display_constitution_query(username: str, language: str):
    if constitution_query_templates := language_metadata[language]['translations'].get('constitutionQuery'):
        constitution_queries = map(lambda query_corpus: query_corpus.replace('{}', username), constitution_query_templates)
    else:
        constitution_queries = map(lambda query_corpus: query_corpus + f' {username}?', [f"What's up", f"How are you"])

    output.centered(random.choice(list(constitution_queries)), view.VERTICAL_OFFSET)


def _display_training_item_sequence(training_item_sequence_plot_data: SequencePlotData):
    y_label_max_length = max(map(lambda label: len(str(label)), training_item_sequence_plot_data.sequence))
    outer_left_x_label = 'two weeks ago'
    color = [asciiplot.Color.BLUE, asciiplot.Color.RED][training_item_sequence_plot_data.item_name.startswith('s')]

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
