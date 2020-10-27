from typing import List

from nltk.stem import SnowballStemmer
from termcolor import colored

from lingularity.backend.utils import spacy
from lingularity.backend.database import MongoDBClient
from lingularity.backend.ops.google.text_to_speech import google_tts
from lingularity.backend.resources import strings as string_resources
from lingularity.backend.metadata import language_metadata

from .ops.reference_language import get_english_reference_language
from lingularity.frontend.console.state import State
from lingularity.frontend.console.utils import output, view, input_resolution


@view.view_creator(header='ELIGIBLE LANGUAGES', title='Add a new Language')
def __call__():
    train_english = False

    eligible_languages = list(set(language_metadata.keys()) - set(MongoDBClient.get_instance().query_trained_languages()))

    starting_letter_grouped_languages = output.group_by_starting_letter(eligible_languages, is_sorted=False)
    colored_joined_language_groups = ['  '.join(map(_color_language_wrt_available_components, language_group)) for language_group in starting_letter_grouped_languages]
    indentation = output.centered_block_indentation(colored_joined_language_groups)
    for language_group in colored_joined_language_groups:
        print(indentation, language_group)

    # TODO: display legend

    # query desired language
    selection = input_resolution.query_relentlessly(f'{output.SELECTION_QUERY_OUTPUT_OFFSET}Select language: ', options=eligible_languages)

    # query desired reference language if English selected
    if selection == string_resources.ENGLISH:
        train_english = True
        selection = get_english_reference_language(eligible_languages=eligible_languages)

    State.set_language(non_english_language=selection, train_english=train_english)


def _color_language_wrt_available_components(language: str) -> str:
    color, attrs = None, None

    if google_tts.available_for(language):
        attrs = ['bold']

    if language in spacy.ELIGIBLE_LANGUAGES:
        color = 'red'
    elif language.lower() in SnowballStemmer.languages:
        color = 'magenta'
    else:
        color = 'cyan'

    return colored(language, color=color, attrs=attrs)
