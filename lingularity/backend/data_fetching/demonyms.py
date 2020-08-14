from typing import *

from bs4 import BeautifulSoup

from .utils.page_source_reading import read_page_source


def fetch_demonyms(country_name: str) -> Optional[Iterator[str]]:
    """
        Args:
            country_name: uppercase """

    page_url = f'http://en.wikipedia.org/wiki/{country_name}'

    soup: BeautifulSoup = read_page_source(page_url)
    demonym_tag = soup.find('a', href='/wiki/Demonym')

    if demonym_tag is None:
        return None

    is_demonym = lambda demonym_candidate: demonym_candidate[:2] == country_name[:2]

    first_demonym_fetched = False
    for element in list(demonym_tag.next_elements)[1:10]:
        if element.name is None:
            if not first_demonym_fetched:
                yield element
                first_demonym_fetched = True
            elif first_demonym_fetched and is_demonym(element):
                yield element
