from typing import Optional, List
import os
import random

from lingularity.backend.utils.data_storing import load_json
from .types import (
    SubstitutionForenamesMap,
    LanguageMetadata,
    CountryMetadata,
    DefaultForenamesTranslations
)


METADATA_DIR_PATH = f'{os.getcwd()}/lingularity/backend/resources/metadata'


language_metadata: LanguageMetadata = load_json(f'{METADATA_DIR_PATH}/language')
_country_metadata: CountryMetadata = load_json(f'{METADATA_DIR_PATH}/country')


def replacement_forenames_available_for(language: str) -> bool:
    if (countries_language_employed_in := _countries_language_employed_in(language)) is None:
        return False
    return bool(_data_beset_countries(countries_language_employed_in))


def get_substitution_forenames_map(language: str) -> SubstitutionForenamesMap:
    """ Returns:
            replacement forename data of randomly picked country passed language
            employed in

        Assumes previous assertion of replacement forenames being available for language """

    assert (countries_language_employed_in := _countries_language_employed_in(language)) is not None
    country = random.choice(_data_beset_countries(countries_language_employed_in))
    assert (substitution_forenames_map := _country_metadata[country]) is not None
    return substitution_forenames_map


def _countries_language_employed_in(language: str) -> Optional[List[str]]:
    return language_metadata[language]['countriesEmployedIn']


def _data_beset_countries(countries_language_employed_in: List[str]) -> List[str]:
    return list(filter(_country_metadata.get, countries_language_employed_in))
