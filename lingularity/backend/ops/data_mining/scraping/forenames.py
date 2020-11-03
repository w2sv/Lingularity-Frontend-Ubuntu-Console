from typing import Optional, List

from lingularity.backend.utils.strings import strip_multiple
from .utils import read_page_source


_POPULAR_FORENAMES_PAGE_URL = 'http://en.wikipedia.org/wiki/List_of_most_popular_given_names'

popular_forenames_page_source: List[str] = str(read_page_source(_POPULAR_FORENAMES_PAGE_URL)).split('\n')


def scrape(country: str) -> Optional[List[List[List[str]]]]:
    """
        Returns:
            None in case of irretrievability of both popular male and female forenames, otherwise
            [male_forenames: List[str], female_forenames: List[str]] """

    forename_block_initiating_row_indices = _get_forename_block_preceding_row_indices(country=country)

    if len(forename_block_initiating_row_indices) < 2:
        return None

    first_forename_possessing_row_indices = [index + 1 for index in forename_block_initiating_row_indices]
    return list(map(_scrape_forenames, first_forename_possessing_row_indices))


def _get_forename_block_preceding_row_indices(country: str) -> List[int]:
    forename_block_initiating_row_indices: List[int] = []

    for i, row in enumerate(popular_forenames_page_source):
        if country in row and (row.endswith(f'</a></sup></td>') or popular_forenames_page_source[i - 1] == '<tr>'):
            if len(forename_block_initiating_row_indices):
                if i - forename_block_initiating_row_indices[0] >= 13:
                    forename_block_initiating_row_indices.append(i)
                    break
            else:
                forename_block_initiating_row_indices.append(i)

    return forename_block_initiating_row_indices


def _scrape_forenames(forename_possessing_row_index: int) -> List[List[str]]:
    EXIT_ELEMENTS = ['sup class="reference"', '</td></tr>']
    BRACKETS = list('()')
    possesses_foreign_transcription = False
    spelling_kinds: List[List[str]] = [[] for _ in range(2)]

    while all(exit_element not in (row := popular_forenames_page_source[forename_possessing_row_index]) for exit_element in EXIT_ELEMENTS):
        truncated_row = row[5:] if 'href' in row else row[3:]  # <td><a href... -> a href...

        extracted_forename = truncated_row[truncated_row.find('>') + 1:truncated_row.find('<')].split('/')[0]
        if len((stripped_forename := extracted_forename.strip())) > 1 and stripped_forename != 'NA':
            truncated_row += '</td>'

            forename_transcriptions = []
            if all(bracket in extracted_forename for bracket in BRACKETS):
                possesses_foreign_transcription = True
                forename_transcriptions = [forename.strip() for forename in strip_multiple(extracted_forename, strings=BRACKETS).split(' ')]

            elif '</a>' in truncated_row and len((forename_transcription := truncated_row[truncated_row.find('</a>') + len('</a>'):truncated_row.find('</td>')])):
                possesses_foreign_transcription = True
                forename_transcriptions = [extracted_forename, strip_multiple(forename_transcription, strings=[' '] + BRACKETS)]

            elif not possesses_foreign_transcription:
                forename_transcriptions = [extracted_forename]

            for i, transcription in enumerate(forename_transcriptions):
                spelling_kinds[i].append(transcription)

        forename_possessing_row_index += 1

    for i, spellings in enumerate(spelling_kinds):
        spelling_kinds[i] = list(dict.fromkeys(filter(lambda candidate: 0 < len(candidate) < 20, (candidate.split(',')[0] for candidate in spellings))))

    return spelling_kinds


if __name__ == '__main__':
    from time import time

    t1 = time()
    print(scrape('New Zealand'))
    print(f'took {time() - t1}s')
