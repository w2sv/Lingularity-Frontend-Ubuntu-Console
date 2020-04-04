from typing import Dict
import os
import warnings

import urllib.request
import requests
from bs4 import BeautifulSoup
import zipfile

warnings.filterwarnings('ignore')


class AppUrlOpener(urllib.request.FancyURLopener):
    version = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.69 Safari/537.36'


urllib._urlopener = AppUrlOpener()


class ContentRetriever:
    PAGE_URL = 'http://www.manythings.org/anki'

    def __init__(self):
        self.languages_2_ziplinks = self._get_language_ziplink_dict()

    def _get_language_ziplink_dict(self) -> Dict[str, str]:
        FLAG_URL = 'http://www.manythings.org/img/usa.png'  # preceding every zip link row

        response = requests.get(self.PAGE_URL, headers={'User-Agent': 'XY'})  # specific header for erroneous response 406 resolution
        response_code = int(''.join(filter(lambda c: c.isdigit(), str(response))))
        if response_code != 200:
            print('Erroneous webpage response')
            return {}

        page_content = str(BeautifulSoup(response.text, "html.parser"))
        download_link_rows = page_content[page_content.find(FLAG_URL):page_content.rfind(FLAG_URL)].split('\n')
        relevant_columns = (row.split('\t')[1:][0] for row in download_link_rows[:-1])
        language_2_ziplink = {row[:row.find(' ')]: row[row.find('"')+1:row.rfind('"')] for row in relevant_columns}
        return language_2_ziplink

    def download_zipfile(self, language: str) -> str:
        zip_link = f'{self.PAGE_URL}/{self.languages_2_ziplinks[language]}'
        save_destination_dir = os.path.join(os.path.join(os.getcwd(), 'SentencePairData'), language)
        if not os.path.exists(save_destination_dir):
            os.makedirs(save_destination_dir)

        save_destination_link = os.path.join(save_destination_dir, f'{language}.zip')
        print('Downloading sentence data...')
        urllib._urlopener.retrieve(zip_link, save_destination_link)
        return save_destination_link

    def unzip_file(self, zip_file_link):
        language_dir_link = zip_file_link[:zip_file_link.rfind(os.sep)]
        with zipfile.ZipFile(zip_file_link, 'r') as zip_ref:
            zip_ref.extractall(language_dir_link)

        # remove unpacked zip file, about.txt
        os.remove(zip_file_link)
        os.remove(os.path.join(language_dir_link, '_about.txt'))


if __name__ == '__main__':
    content_retriever = ContentRetriever()
    content_retriever.unzip_file(r'C:\Users\User\Documents\download.zip')
