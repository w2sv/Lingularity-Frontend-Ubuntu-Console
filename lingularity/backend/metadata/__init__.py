from typing import Optional, List
import json
import os
import random
import sys

from .types import ReplacementForenames, LanguageMetadata, CountryMetadata, DefaultForenamesTranslations


METADATA_DIR_PATH = f'{os.getcwd()}/lingularity/backend/resources/metadata'


def _load_metadata(file_name: str):
    if 'Mine' in sys.argv:
        return {}
    return json.load(open(f'{METADATA_DIR_PATH}/{file_name}.json', 'r', encoding='utf-8'))


language_metadata: LanguageMetadata = _load_metadata('language')
_country_metadata: CountryMetadata = _load_metadata('country')


def get_replacement_forenames(language: str) -> Optional[ReplacementForenames]:
    countries_language_employed_in: Optional[List[str]] = language_metadata[language]['countriesEmployedIn']

    if countries_language_employed_in is None:
        return None

    data_beset_countries: List[str] = list(filter(_country_metadata.get, countries_language_employed_in))

    if len(data_beset_countries):
        return _country_metadata[random.choice(data_beset_countries)]
    return None
