from typing import Dict, List, Optional
import os
import warnings
import logging

import urllib.request
import zipfile

from lingularity.backend.data_fetching.utils.page_source_reading import read_page_source

warnings.filterwarnings('ignore')


# TODO: debug telugu, north download


class AppUrlOpener(urllib.request.FancyURLopener):
    version = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.69 Safari/537.36'


_patched_urllib = urllib
_patched_urllib._urlopener = AppUrlOpener()  # type: ignore


class SentenceDataFetcher:
    SENTENCE_DATA_PAGE_URL = 'http://www.manythings.org/anki'
    BASE_SAVE_DESTINATION_DIR_PATH = f'{os.getcwd()}/language_data'

    language_2_ziplink: Optional[Dict[str, str]] = None

    def __init__(self):
        if self.language_2_ziplink is None:
            self.language_2_ziplink = self._scrape_language_2_downloadlink_dict()

    @staticmethod
    def _scrape_language_2_downloadlink_dict() -> Dict[str, str]:
        FLAG_URL = 'http://www.manythings.org/img/usa.png'  # initiating every zip link row

        page_content = str(read_page_source(SentenceDataFetcher.SENTENCE_DATA_PAGE_URL))
        download_link_rows = page_content[page_content.find(FLAG_URL):page_content.rfind(FLAG_URL)].split('\n')
        relevant_columns = (row.split('\t')[1:][0] for row in download_link_rows[:-1])
        return {row[:row.find(' ')]: row[row.find('"') + 1:row.rfind('"')] for row in relevant_columns}

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

        logging.info(f'Downloaded {n_downloaded_language_files} language files')

    def _download_zipfile(self, language: str) -> str:
        """
            Returns:
                absolute zip file save destination path """

        download_link = f'{self.SENTENCE_DATA_PAGE_URL}/{self.language_2_ziplink[language]}'
        save_destination_dir = f'{self.BASE_SAVE_DESTINATION_DIR_PATH}/{language}'
        if not os.path.exists(save_destination_dir):
            os.makedirs(save_destination_dir)

        save_destination_link = os.path.join(save_destination_dir, f'{language}.zip')
        _patched_urllib._urlopener.retrieve(download_link, save_destination_link)  # type: ignore
        logging.info(f'Downloaded {language} sentence data')
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
