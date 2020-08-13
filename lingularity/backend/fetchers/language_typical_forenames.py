from typing import *
import re

import requests
from bs4 import BeautifulSoup

from .patching import patched_urllib


def fetch_language_corresponding_countries(language: str) -> Tuple[str]:
    """ uppercase language """

    page_url = f'http://en.wikipedia.org/wiki/{language}_language'

    response = requests.get(page_url, headers={'User-Agent': 'XY'})  # specific header for erroneous response 406 resolution
    if (response_code := int(''.join(filter(lambda c: c.isdigit(), str(response))))) != 200:
        raise ConnectionError('Erroneous webpage response')

    page_content = str(BeautifulSoup(response.text, "html.parser"))
    rows = page_content.split('\n')

    try:
        for i, row in enumerate(rows):
            if 'Official language' in row:
                match = re.findall(r'Flag_of.*.svg', row)[0]
                flag_of_identifiers = set(filter(lambda identifier: identifier.startswith('Flag_of'), match.split('/')))
                countries = list(map(lambda flag_of_identifier: flag_of_identifier[len('Flag_of_'):flag_of_identifier.find('.')], flag_of_identifiers))
                print(countries)
                break
    except IndexError:
        for i, row in enumerate(rows):
            if '<ul class="NavContent" style="list-style: none none; margin-left: 0; text-align: left; font-size: 105%; margin-top: 0; margin-bottom: 0; line-height: inherit;"' in row:
                index = i

                while 'title' in (country_possessing_row := rows[index]):
                    country = country_possessing_row[country_possessing_row[:-1].rfind('>')+1:country_possessing_row.rfind('<')]
                    if not len(country.strip()):
                        title_starting_row = country_possessing_row[country_possessing_row.find('title') + len('title'):]
                        country = title_starting_row[title_starting_row.find('>') + 1:title_starting_row.find('<')]
                    print(country)
                    index += 1
                break



def fetch_typical_forenames(language: str) -> List[Tuple[str]]:
    PAGE_URL = 'http://en.wikipedia.org/wiki/List_of_most_popular_given_names'

    corresponding_country = 'Germany'

    response = requests.get(PAGE_URL, headers={'User-Agent': 'XY'})  # specific header for erroneous response 406 resolution
    if (response_code := int(''.join(filter(lambda c: c.isdigit(), str(response))))) != 200:
        raise ConnectionError('Erroneous webpage response')

    page_content = str(BeautifulSoup(response.text, "html.parser"))
    href_row_data = [row for row in page_content.split('\n') if 'href' in row]

    name_block_initiating_row_indices = [i for i, row in enumerate(href_row_data) if row.endswith(f'</a></sup></td>') and corresponding_country in row]

    def scrape_names(name_block_initiating_row_index: int) -> Iterator[str]:
        row_index = name_block_initiating_row_index + 1
        while 'sup class="reference"' not in (row := href_row_data[row_index]):
            init_tag_less_row = row[5:]
            yield init_tag_less_row[init_tag_less_row.find('>')+1:init_tag_less_row.find('<')].split('/')[0]
            row_index += 1

    return [tuple(scrape_names(row_index)) for row_index in name_block_initiating_row_indices]

if __name__ == '__main__':
    fetch_language_corresponding_countries('Italian')

    # fetch_typical_forenames('Italian')