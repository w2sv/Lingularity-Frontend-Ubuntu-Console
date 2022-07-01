import random
from typing import Optional

import asciiplot
from backend.src.database import UserMongoDBClient
from backend.src.metadata import language_metadata

from frontend.src.reentrypoint import ReentryPoint
from frontend.src.option import Option, OptionCollection
from frontend.src.state import State
from frontend.src.trainers.sentence_translation import SentenceTranslationTrainerFrontend
from frontend.src.trainers.sequence_plot_data import SequencePlotData
from frontend.src.trainers.trainer_frontend import TrainerFrontend
from frontend.src.trainers.vocable_adder import VocableAdderFrontend
from frontend.src.trainers.vocable_trainer import VocableTrainerFrontend
from frontend.src.utils import output, view
from frontend.src.utils.prompt.cancelling import QUERY_CANCELLED
from frontend.src.utils.prompt.repetition import prompt_relentlessly
from frontend.src.utils.view import Banner, terminal


@view.creator(banner=Banner('lingularity/3d-ascii', 'green'))
@State.receiver
def __call__(state: State, training_item_sequence_plot_data: Optional[SequencePlotData] = None) -> ReentryPoint:
    terminal.set_title(f'{state.language} Training Selection')

    if training_item_sequence_plot_data:
        _display_training_item_sequence(training_item_sequence_plot_data)
    else:
        _display_constitution_query(username=state.username, language=state.language)

    options = _get_options()

    # query desired action
    if (action_selection_keyword := _query_action_selection(options)) == QUERY_CANCELLED:
        return ReentryPoint.Home

    callback = options[action_selection_keyword]

    # instantiate frontend if selected
    if issubclass(callback, TrainerFrontend):
        trainer_frontend = callback()
        return __call__(training_item_sequence_plot_data=trainer_frontend.__call__())
    return callback


@UserMongoDBClient.receiver
def _get_options(user_mongo_client: UserMongoDBClient) -> OptionCollection:
    options = [Option('sentences', 'Translate Sentences', callback=SentenceTranslationTrainerFrontend)]

    if user_mongo_client.language in user_mongo_client.query_vocabulary_possessing_languages():
        options.append(Option('vocabulary', 'Train Vocabulary', callback=VocableTrainerFrontend))

    options.append(Option('add', 'Add Vocabulary', callback=VocableAdderFrontend))
    options.append(Option('quit', 'Quit', callback=ReentryPoint.Exit))

    return OptionCollection(options)


def _query_action_selection(options: OptionCollection) -> str:
    output.centered(options.as_row(), '\n')
    return prompt_relentlessly(
        prompt=output.centering_indentation(' '),
        options=list(options),
        cancelable=True
    )


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
