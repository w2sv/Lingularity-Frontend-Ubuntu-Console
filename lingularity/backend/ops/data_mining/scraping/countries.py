import re
from typing import Optional, List, Set

from .utils import read_page_source


def _rectify_country_names(country_list: List[str]) -> Set[str]:
    REPR_2_ACTUAL = {'Mainland China': 'China',
                     'the_People%27s_Republic_of_China': 'China',
                     'Denmark_%28state%29': 'Denmark',
                     'Belgium_%28civil%29': 'Belgium',
                     'New_Zealand': 'New Zealand',
                     'South_Africa': 'South Africa'}

    BLACKLIST = {'%C3%85land', 'Europe'}

    for i, country in enumerate(country_list):
        if (actual_country := REPR_2_ACTUAL.get(country)) is not None:
            country_list[i] = actual_country

        elif country in BLACKLIST:
            country_list.remove(country)

        else:
            country_list[i] = country.lstrip('the_')

    return set(country_list)


def scrape(language: str) -> Optional[Set[str]]:
    """
        Args:
            language: uppercase """

    language_page_url = f'http://en.wikipedia.org/wiki/{language}_language'

    page_source: List[str] = str(read_page_source(language_page_url)).split('\n')

    for i, row in enumerate(page_source):
        if 'Official language' in row:
            try:
                match = re.findall(r'Flag_of.*.svg', row)[0]
                flag_of_identifiers = set(filter(lambda identifier: identifier.startswith('Flag_of'), match.split('/')))
                return _rectify_country_names(list(map(lambda flag_of_identifier: flag_of_identifier[len('Flag_of_'):flag_of_identifier.find('.')], flag_of_identifiers)))
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
            return _rectify_country_names(countries)
    return None


if __name__ == '__main__':
    print(scrape('English'))