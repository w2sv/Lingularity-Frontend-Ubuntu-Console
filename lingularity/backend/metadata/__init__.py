import json
import os
import random
from typing import Optional, List

from .types import ForenameConversionData, LanguageMetadata, CountryMetadata


METADATA_DIR_PATH = f'{os.getcwd()}/.metadata'


def _load_metadata(file_name: str):
    return json.load(open(f'{METADATA_DIR_PATH}/{file_name}.json', 'r', encoding='utf-8'))


language_metadata: LanguageMetadata = None
_country_metadata: CountryMetadata = None


if len(os.listdir(METADATA_DIR_PATH)):
    language_metadata, _country_metadata = list(map(_load_metadata, ['languages', 'countries']))


def get_forename_conversion_data(language: str) -> Optional[ForenameConversionData]:
    countries_language_employed_in: Optional[List[str]] = language_metadata[language]['countriesEmployedIn']

    if countries_language_employed_in is None:
        return None

    data_beset_countries: List[str] = list(filter(_country_metadata.get, countries_language_employed_in))

    if len(data_beset_countries):
        return _country_metadata[random.choice(data_beset_countries)]
    return None
