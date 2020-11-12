from typing import List

from backend import string_resources
from backend import MongoDBClient
from frontend.utils import query, output


def procure(eligible_languages: List[str]) -> str:
    """ Procures English reference language from either database or
        user if unsuccessful, enters selection into database in case
        of the latter """

    if not (selection := query_database()):
        output.erase_lines(2)

        selection = _query_user(eligible_languages)
        MongoDBClient.get_instance().set_reference_language(reference_language=selection)

    return selection


def _query_user(eligible_languages: List[str]) -> str:
    eligible_languages.remove(string_resources.ENGLISH)
    selection = query.relentlessly(
        f'{query.horizontal_indentation()}Select reference language: ',
        options=eligible_languages
    )

    return selection

def query_database():
    return MongoDBClient.get_instance().query_reference_language()
