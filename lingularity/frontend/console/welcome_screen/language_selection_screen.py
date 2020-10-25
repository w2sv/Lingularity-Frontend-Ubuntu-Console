from typing import Tuple
from itertools import groupby

from nltk.stem import SnowballStemmer
from termcolor import colored

from lingularity.backend.utils import spacy
from lingularity.backend.ops.google.text_to_speech import google_tts
from lingularity.backend.database import MongoDBClient
from lingularity.backend.resources import strings as string_resources
from lingularity.backend.metadata import language_metadata

from lingularity.frontend.console.utils.view import view_creator
from lingularity.frontend.console.utils.input_resolution import resolve_input, repeat, indicate_indissolubility
from lingularity.frontend.console.utils.console import (
    centered_block_indentation,
    erase_lines,
    SELECTION_QUERY_OUTPUT_OFFSET,
    ansi_escape_code_stripped
)


@view_creator(header='ELIGIBLE LANGUAGES')
def select_language() -> Tuple[str, bool]:
    """ Returns:
            non-english language: str
            train_english: bool """

    train_english = False

    mongodb_client = MongoDBClient.get_instance()
    eligible_languages = list(language_metadata.keys())

    for i, language in enumerate(eligible_languages):
        color, attrs = None, None

        if google_tts.available_for(language):
            attrs = ['bold']

        if language in spacy.ELIGIBLE_LANGUAGES:
            color = 'red'
        elif language.lower() in SnowballStemmer.languages:
            color = 'magenta'
        else:
            color = 'cyan'

        eligible_languages[i] = colored(language, color=color, attrs=attrs)

    starting_letter_grouped_languages = ['  '.join(list(v)) for _, v in groupby(eligible_languages, lambda x: ansi_escape_code_stripped(x)[0])]
    indentation = centered_block_indentation(starting_letter_grouped_languages)
    for language_group in starting_letter_grouped_languages:
        print(indentation, language_group)

    # TODO: display legend

    # query desired language
    if (selection := resolve_input(input(f'{SELECTION_QUERY_OUTPUT_OFFSET}Select language: '), eligible_languages)) is None:
        return repeat(select_language, n_deletion_lines=-1)

    # query desired reference language if English selected
    elif selection == string_resources.ENGLISH:
        train_english, selection = True, mongodb_client.query_reference_language()
        eligible_languages.remove(string_resources.ENGLISH)

        erase_lines(2)

        while selection is None:
            if (selection := resolve_input(input(f'{SELECTION_QUERY_OUTPUT_OFFSET}Select reference language: '), eligible_languages)) is None:
                indicate_indissolubility(n_deletion_lines=2)
            else:
                mongodb_client.set_reference_language(reference_language=selection)

    return selection, train_english
