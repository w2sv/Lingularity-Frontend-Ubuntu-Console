from typing import Dict

from .utils import read_page_source


SENTENCE_DATA_PAGE_URL = 'http://www.manythings.org/anki'


def scrape_sentence_data_download_links() -> Dict[str, str]:
    FLAG_URL = 'http://www.manythings.org/img/usa.png'  # initiating every zip link row

    page_content = str(read_page_source(SENTENCE_DATA_PAGE_URL))
    download_link_rows = page_content[page_content.find(FLAG_URL):page_content.rfind(FLAG_URL)].split('\n')
    relevant_columns = (row.split('\t')[1:][0] for row in download_link_rows[:-1])
    return {row[:row.find(' ')]: row[row.find('"') + 1:row.rfind('"')] for row in relevant_columns}
