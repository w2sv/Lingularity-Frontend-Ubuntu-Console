from typing import Optional, List
import random
import logging

from lingularity.backend import META_DATA_PATH
from lingularity.backend.utils.data import load_json
from .types import (
    SubstitutionForenamesMap,
    LanguageMetadata,
    CountryMetadata,
    DefaultForenamesTranslations
)


language_metadata: LanguageMetadata = load_json(f'{META_DATA_PATH}/language')
_country_metadata: CountryMetadata = load_json(f'{META_DATA_PATH}/country')


def get_substitution_forenames_map(language: str) -> SubstitutionForenamesMap:
    """ Returns:
            replacement forename data of randomly picked country passed language
            is used in

        Assumes previous assertion of replacement forenames being available for language """

    data_beset_countries = data_beset_countries_language_employed_in(language=language)
    assert data_beset_countries is not None
    country = random.choice(data_beset_countries)
    assert (substitution_forenames_map := _country_metadata[country]) is not None

    # add country to forenames map
    substitution_forenames_map['country'] = country

    logging.info(f'Using forenames originating from {country}')

    return substitution_forenames_map


def data_beset_countries_language_employed_in(language: str) -> Optional[List[str]]:
    uses_latin_script = language_metadata[language]['properties']['usesLatinScript']
    countries_language_employed_in = language_metadata[language]['countriesEmployedIn']

    def contains_applicable_data(country: str) -> bool:
        def native_forenames_available(_substitution_forenames_map: SubstitutionForenamesMap):
            return all([_substitution_forenames_map['maleForenames']['nativeSpelling'], _substitution_forenames_map['femaleForenames']['nativeSpelling']])

        if not (substitution_forenames_map := _country_metadata.get(country)):
            return False
        return uses_latin_script or native_forenames_available(substitution_forenames_map)

    data_beset_countries = list(filter(contains_applicable_data, countries_language_employed_in))
    return [None, data_beset_countries][bool(data_beset_countries)]
