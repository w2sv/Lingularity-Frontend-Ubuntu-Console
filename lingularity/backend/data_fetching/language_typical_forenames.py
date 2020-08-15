from typing import Optional, List, Tuple
import re
from random import shuffle
import logging

from lingularity.backend.data_fetching.utils.page_source_reading import read_page_source


POPULAR_FORENAMES_PAGE_URL = 'http://en.wikipedia.org/wiki/List_of_most_popular_given_names'


def scrape_language_typical_forenames(language: str) -> Tuple[Optional[List[List[str]]], Optional[str]]:
    """
        Args:
            language: uppercase
        Returns:
            [male_forenames: List[str], female_forenames: List[str]], corresponding valid random country: str """

    logging.info(f'language: {language}')
    ERROR_CASE_RETURN_VALUE = (None, None)

    if (countries_language_employed_in := _scrape_countries_language_employed_in(language)) is None:
        logging.info("Couldn't find any countries language is employed in")
        return ERROR_CASE_RETURN_VALUE

    logging.info(f'countries_language_employed_in: {countries_language_employed_in}')

    shuffle(countries_language_employed_in)
    page_source: List[str] = str(read_page_source(POPULAR_FORENAMES_PAGE_URL)).split('\n')

    for country in countries_language_employed_in:
        if (forename_lists := _scrape_popular_forenames(country, popular_forenames_page_source=page_source)) is not None and all(forename_lists):
            logging.info(f'forename_country: {country}')
            logging.info(f'forename_lists: {forename_lists}')
            return forename_lists, country
    logging.info("Couldn't find any forenames")
    return ERROR_CASE_RETURN_VALUE


def _scrape_countries_language_employed_in(language: str) -> Optional[List[str]]:
    """
        Args:
            language: uppercase """

    language_page_url = f'http://en.wikipedia.org/wiki/{language}_language'

    def _correct_corrupted_country_names(country_list: List[str]) -> List[str]:
        repr_2_actual = {'Mainland China': 'China',
                         'the_People%27s_Republic_of_China': 'China',
                         'the_Philippines': 'Philippines',
                         'the_Czech_Republic': 'Czech_Republic'}

        for i, country in enumerate(country_list):
            if (actual_country := repr_2_actual.get(country)) is not None:
                country_list[i] = actual_country
        return country_list

    page_source: List[str] = str(read_page_source(language_page_url)).split('\n')
    for i, row in enumerate(page_source):
        if 'Official language' in row:
            try:
                match = re.findall(r'Flag_of.*.svg', row)[0]
                flag_of_identifiers = set(filter(lambda identifier: identifier.startswith('Flag_of'), match.split('/')))
                return _correct_corrupted_country_names(list(map(lambda flag_of_identifier: flag_of_identifier[len('Flag_of_'):flag_of_identifier.find('.')], flag_of_identifiers)))
            except IndexError:
                pass

        elif '<ul class="NavContent" style="list-style: none none; margin-left: 0; text-align: left; font-size: 105%; margin-top: 0; margin-bottom: 0; line-height: inherit;"' in row:
            countries = []
            while 'title' in (country_possessing_row := page_source[i]):
                country = country_possessing_row[country_possessing_row[:-1].rfind('>')+1:country_possessing_row.rfind('<')]
                if not len(country.strip()):
                    title_starting_row = country_possessing_row[country_possessing_row.find('title') + len('title'):]
                    country = title_starting_row[title_starting_row.find('>') + 1:title_starting_row.find('<')]
                countries.append(country)
                i += 1
            return _correct_corrupted_country_names(countries)
    return None


def _scrape_popular_forenames(country: str, popular_forenames_page_source: Optional[List[str]] = None) -> Optional[List[List[str]]]:
    """
        Returns:
            None in case of irretrievability of both popular male and female forenames, otherwise
            [male_forenames: List[str], female_forenames: List[str]] """

    # TODO: debug Pakistan

    if popular_forenames_page_source is None:
        popular_forenames_page_source = str(read_page_source(POPULAR_FORENAMES_PAGE_URL)).split('\n')

    # get forename block initiating row indices
    forename_block_initiating_row_indices: List[int] = []
    for i, row in enumerate(popular_forenames_page_source):
        if row.endswith(f'</a></sup></td>') and country in row:
            forename_block_initiating_row_indices.append(i)
            if len(forename_block_initiating_row_indices) == 2:
                break

    # exit in case of incapability to retrieve both male and female forename blocks
    if len(forename_block_initiating_row_indices) != 2:
        return None

    def scrape_forenames(forename_block_initiating_row_index: int) -> List[str]:
        assert popular_forenames_page_source is not None

        forename_possessing_row_index = forename_block_initiating_row_index + 1
        EXIT_ELEMENTS = ['sup class="reference"', '</td></tr>']
        forenames = []

        while all(exit_element not in (row := popular_forenames_page_source[forename_possessing_row_index]) for exit_element in EXIT_ELEMENTS):
            truncated_row = row[5:] if 'href' in row else row[3:]  # <td><a href... -> a href...
            forenames.append(truncated_row[truncated_row.find('>') + 1:truncated_row.find('<')].split('/')[0])
            forename_possessing_row_index += 1
        return list(filter(lambda forename: len(forename) > 2 or not forename.startswith('N'), forenames))

    return list(map(scrape_forenames, forename_block_initiating_row_indices))


if __name__ == '__main__':
    from time import time

    t1 = time()
    print(_scrape_popular_forenames('Korea'))
    print(f'took {time() - t1}s')
