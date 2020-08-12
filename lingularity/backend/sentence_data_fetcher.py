from typing import Dict, List
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


urllib._urlopener = AppUrlOpener()  # type: ignore


class SentenceDataFetcher:
    PAGE_URL = 'http://www.manythings.org/anki'
    BASE_SAVE_DESTINATION_DIR_PATH = f'{os.getcwd()}/language_data'

    def __init__(self):
        self.language_2_ziplink: Dict[str, str] = self._get_language_2_ziplink_dict()

    @staticmethod
    def _get_language_2_ziplink_dict() -> Dict[str, str]:
        FLAG_URL = 'http://www.manythings.org/img/usa.png'  # initiating every zip link row

        response = requests.get(SentenceDataFetcher.PAGE_URL, headers={'User-Agent': 'XY'})  # specific header for erroneous response 406 resolution
        response_code = int(''.join(filter(lambda c: c.isdigit(), str(response))))
        if response_code != 200:
            raise ConnectionError('Erroneous webpage response')

        page_content = str(BeautifulSoup(response.text, "html.parser"))
        download_link_rows = page_content[page_content.find(FLAG_URL):page_content.rfind(FLAG_URL)].split('\n')
        relevant_columns = (row.split('\t')[1:][0] for row in download_link_rows[:-1])
        return {row[:row.find(' ')]: row[row.find('"') + 1:row.rfind('"')] for row in relevant_columns}

    def _download_zipfile(self, language: str) -> str:
        """
            Returns:
                absolute zip file save destination path """

        print('Downloading sentence data...')
        zip_link = f'{self.PAGE_URL}/{self.language_2_ziplink[language]}'
        save_destination_dir = f'{self.BASE_SAVE_DESTINATION_DIR_PATH}/{language}'
        if not os.path.exists(save_destination_dir):
            os.makedirs(save_destination_dir)

        save_destination_link = os.path.join(save_destination_dir, f'{language}.zip')
        urllib._urlopener.retrieve(zip_link, save_destination_link)  # type: ignore
        return save_destination_link

    @staticmethod
    def _unzip_file(zip_file_link: str):
        language_dir_link = zip_file_link[:zip_file_link.rfind(os.sep)]
        with zipfile.ZipFile(zip_file_link, 'r') as zip_ref:
            zip_ref.extractall(language_dir_link)

        # remove unpacked zip file, about.txt
        os.remove(zip_file_link)
        os.remove(os.path.join(language_dir_link, '_about.txt'))

        # rename sentence data file
        os.rename(os.path.join(language_dir_link, os.listdir(language_dir_link)[0]), os.path.join(language_dir_link, 'sentence_data.txt'))

    def fetch_sentence_data_file(self, language: str):
        zip_file_path = self._download_zipfile(language)
        self._unzip_file(zip_file_path)

    def fetch_all_available_sentence_data_files(self):
        locally_available_language_files: List[str] = os.listdir(self.BASE_SAVE_DESTINATION_DIR_PATH)

        n_downloaded_language_files = 0
        for language in self.language_2_ziplink.keys():
            if language not in locally_available_language_files:
                self.fetch_sentence_data_file(language)
                n_downloaded_language_files += 1

        print(f'Downloaded {n_downloaded_language_files} language files')
