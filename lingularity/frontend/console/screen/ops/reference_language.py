from typing import List

from lingularity.backend.database import MongoDBClient
from lingularity.backend.resources import strings as string_resources
from lingularity.frontend.console.utils import output, input_resolution


def get_english_reference_language(eligible_languages: List[str]) -> str:
    selection = query_english_reference_language()

    if not selection:
        output.erase_lines(2)

        eligible_languages.remove(string_resources.ENGLISH)
        selection = input_resolution.query_relentlessly(f'{output.SELECTION_QUERY_OUTPUT_OFFSET}Select reference language: ', options=eligible_languages)

        MongoDBClient.get_instance().set_reference_language(reference_language=selection)

    return selection


def query_english_reference_language():
    return MongoDBClient.get_instance().query_reference_language()
