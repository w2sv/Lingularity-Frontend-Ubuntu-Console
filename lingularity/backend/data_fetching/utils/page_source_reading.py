import requests

from bs4 import BeautifulSoup


def read_page_source(page_url: str) -> str:
    response = requests.get(page_url, headers={'User-Agent': 'XY'})  # specific header for erroneous response 406 resolution
    if (int(''.join(filter(lambda c: c.isdigit(), str(response))))) != 200:
        raise ConnectionError('Erroneous webpage response')

    return str(BeautifulSoup(response.text, "html.parser"))
