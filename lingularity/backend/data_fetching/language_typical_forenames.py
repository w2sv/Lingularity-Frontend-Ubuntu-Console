from typing import Iterator, Optional, List, Tuple
import re
from random import shuffle

from lingularity.backend.data_fetching.utils.page_source_reading import read_page_source


def fetch_typical_forenames(language: str) -> Optional[List[Tuple[str]]]:
    """
        Args:
            language: uppercase """

    PAGE_URL = 'http://en.wikipedia.org/wiki/List_of_most_popular_given_names'

    countries_language_officially_employed_in = _fetch_countries_language_officially_employed_in(language)
    if countries_language_officially_employed_in is None:
        return None

    shuffle(countries_language_officially_employed_in)

    page_source_rows = read_page_source(PAGE_URL).split('\n')

    for country in countries_language_officially_employed_in:
        name_block_initiating_row_indices = [i for i, row in enumerate(page_source_rows) if row.endswith(f'</a></sup></td>') and country in row]
        if len(name_block_initiating_row_indices) != 2:
            continue

        def scrape_names(name_block_initiating_row_index: int) -> Iterator[str]:
            row_index = name_block_initiating_row_index + 1
            while 'sup class="reference"' not in (row := page_source_rows[row_index]) and '</td></tr>' not in row:
                initial_brackets_omitting_row = row[5:] if 'href' in row else row[3:]  # <td><a href... -> a href...
                yield initial_brackets_omitting_row[initial_brackets_omitting_row.find('>')+1:initial_brackets_omitting_row.find('<')].split('/')[0]
                row_index += 1

        forenames = [tuple(scrape_names(row_index)) for row_index in name_block_initiating_row_indices]
        if all(len(name_tuple) for name_tuple in forenames):
            print(f'Employing names originating from {country}')
            return forenames


def _fetch_countries_language_officially_employed_in(language: str) -> Optional[List[str]]:
    """
        Args:
            language: uppercase """

    page_url = f'http://en.wikipedia.org/wiki/{language}_language'

    page_source_rows = read_page_source(page_url).split('\n')

    for i, row in enumerate(page_source_rows):
        if 'Official language' in row:
            try:
                match = re.findall(r'Flag_of.*.svg', row)[0]
                flag_of_identifiers = set(filter(lambda identifier: identifier.startswith('Flag_of'), match.split('/')))
                return _correct_corrupted_country_names(list(map(lambda flag_of_identifier: flag_of_identifier[len('Flag_of_'):flag_of_identifier.find('.')], flag_of_identifiers)))
            except IndexError:
                pass

        elif '<ul class="NavContent" style="list-style: none none; margin-left: 0; text-align: left; font-size: 105%; margin-top: 0; margin-bottom: 0; line-height: inherit;"' in row:
            countries = []
            while 'title' in (country_possessing_row := page_source_rows[i]):
                country = country_possessing_row[country_possessing_row[:-1].rfind('>')+1:country_possessing_row.rfind('<')]
                if not len(country.strip()):
                    title_starting_row = country_possessing_row[country_possessing_row.find('title') + len('title'):]
                    country = title_starting_row[title_starting_row.find('>') + 1:title_starting_row.find('<')]
                countries.append(country)
                i += 1
            return _correct_corrupted_country_names(countries)


def _correct_corrupted_country_names(country_list: List[str]) -> List[str]:
    repr_2_actual = {'Mainland China': 'China',
                     'the_Philippines': 'Philippines',
                     'the_Czech_Republic': 'Czech_Republic'}

    for i, country in enumerate(country_list):
        if (actual_country := repr_2_actual.get(country)) is not None:
            country_list[i] = actual_country
    return country_list


if __name__ == '__main__':
    from time import time

    t1 = time()
    print(fetch_typical_forenames('Czech'))
    print(f'took {time() - t1}s')
