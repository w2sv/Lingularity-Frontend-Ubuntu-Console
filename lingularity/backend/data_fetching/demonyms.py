from typing import *

from .utils.page_source_reading import read_page_source


# def fetch_demonyms(country_name: str) -> Optional[List[str]]:
#
#     page_url = f'http://en.wikipedia.org/wiki/{country_name}'
#
#     page_source_rows = read_page_source(page_url).split('\n')
#
#     for row in page_source_rows:
#         if 'Demonym' in row:
#             start_tags = ['</a></th><td>', '</a></sup><br/>']
#             end_tag = ['<sup', '</a></li><li><a', '</a></li></ul></div></td></tr><tr><th']
#
#             demonym_tag_starting_row = row[row.find('Demonym'):]
#             demonyms = []
#             for start_tag in start_tags:
#                 if (start_tag_index := demonym_tag_starting_row.find(start_tag)) != -1:
#                     demonyms.append(demonym_tag_starting_row[start_tag_index + len(start_tag):demonym_tag_starting_row[start_tag_index:].find(end_tag) + start_tag_index])
#             return demonyms
#     return None
#
#
# if __name__ == '__main__':
#     fetch_typical_forenames('Sweden')