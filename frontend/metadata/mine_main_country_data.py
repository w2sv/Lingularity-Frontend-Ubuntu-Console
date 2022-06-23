from typing import Dict, Optional

from backend import language_metadata
from backend.utils import io
from textacy.similarity import levenshtein
import numpy as np

from frontend.metadata import COUNTRY_METADATA_PATH, MAIN_COUNTRY_DATA_PATH


# TODO: move to mining repo


if __name__ == '__main__':
    country_metadata = io.load_json(COUNTRY_METADATA_PATH)
    countries = list(country_metadata.keys())

    language_2_main_country: Dict[str, Optional[str]] = {}
    for language in language_metadata.keys():
        # determine employment country possessing max levenshtein wrt language
        # in case of existence of employment countries
        if len((countries_employed_in := language_metadata[language]['countriesEmployedIn'])):
            language_employment_levenshteins = [levenshtein(country, language) for country in countries_employed_in]
            max_levenshtein_country = countries_employed_in[int(np.argmax(language_employment_levenshteins))]

            # use max levenshtein country language employed in if amongst countries possessing flag,
            # otherwise use flag possessing country with max levenshtein to max levenshtein country
            # language employed in
            if (matched_country := country_metadata.get(max_levenshtein_country)) is not None:
                language_2_main_country[language] = max_levenshtein_country
            else:
                max_levenshtein_country_flag_possessing_countries_levenshteins = [levenshtein(max_levenshtein_country, country) for country in countries]
                max_levenshtein_country = countries[int(np.argmax(max_levenshtein_country_flag_possessing_countries_levenshteins))]
                language_2_main_country[language] = max_levenshtein_country
        else:
            language_2_main_country[language] = None

    io.write_json(language_2_main_country, file_path=MAIN_COUNTRY_DATA_PATH)
