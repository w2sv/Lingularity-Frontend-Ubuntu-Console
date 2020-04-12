from typing import Dict, Optional
import os
import warnings

import urllib.request
import requests
from bs4 import BeautifulSoup
import zipfile

warnings.filterwarnings('ignore')


# TODO: debug telugu download


class AppUrlOpener(urllib.request.FancyURLopener):
    version = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.69 Safari/537.36'


urllib._urlopener = AppUrlOpener()


class ContentRetriever:
    PAGE_URL = 'http://www.manythings.org/anki'

    def __init__(self):
        self.languages_2_ziplinks: Optional[Dict[str, str]] = None

    def get_language_ziplink_dict(self):
        FLAG_URL = 'http://www.manythings.org/img/usa.png'  # initiating every zip link row

        try:
            response = requests.get(self.PAGE_URL, headers={'User-Agent': 'XY'})  # specific header for erroneous response 406 resolution
            response_code = int(''.join(filter(lambda c: c.isdigit(), str(response))))
            if response_code != 200:
                print('Erroneous webpage response')
                self.languages_2_ziplinks = None

            page_content = str(BeautifulSoup(response.text, "html.parser"))
            download_link_rows = page_content[page_content.find(FLAG_URL):page_content.rfind(FLAG_URL)].split('\n')
            relevant_columns = (row.split('\t')[1:][0] for row in download_link_rows[:-1])
            self.languages_2_ziplinks = {row[:row.find(' ')]: row[row.find('"')+1:row.rfind('"')] for row in relevant_columns}
        except requests.exceptions.ConnectionError:
            self.languages_2_ziplinks = None

    def download_zipfile(self, language: str) -> str:
        zip_link = f'{self.PAGE_URL}/{self.languages_2_ziplinks[language]}'
        save_destination_dir = os.path.join(os.path.join(os.getcwd(), 'language_data'), language)
        if not os.path.exists(save_destination_dir):
            os.makedirs(save_destination_dir)

        save_destination_link = os.path.join(save_destination_dir, f'{language}.zip')
        print('Downloading sentence data...')
        urllib._urlopener.retrieve(zip_link, save_destination_link)
        return save_destination_link

    @staticmethod
    def unzip_file(zip_file_link):
        language_dir_link = zip_file_link[:zip_file_link.rfind(os.sep)]
        with zipfile.ZipFile(zip_file_link, 'r') as zip_ref:
            zip_ref.extractall(language_dir_link)

        # remove unpacked zip file, about.txt
        os.remove(zip_file_link)
        os.remove(os.path.join(language_dir_link, '_about.txt'))

        # rename sentence data file
        os.rename(os.path.join(language_dir_link, os.listdir(language_dir_link)[0]), os.path.join(language_dir_link, 'sentence_data.txt'))


if __name__ == '__main__':
    content_retriever = ContentRetriever()
    content_retriever.unzip_file(r'C:\Users\User\Documents\download.zip')
