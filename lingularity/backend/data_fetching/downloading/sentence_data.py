""" scrapes language_2_ziplink dict as soon as something from
    the module is getting imported in case of the former not already being set """

from typing import Dict, List, Optional
import os
import warnings
import logging

import zipfile

from lingularity.backend.data_fetching.scraping.sentence_data_download_links import scrape_language_2_downloadlink_dict, SENTENCE_DATA_PAGE_URL
from .utils import patched_urllib

warnings.filterwarnings('ignore')
# TODO: debug telugu, north download


_BASE_SAVE_DESTINATION_DIR_PATH = f'{os.getcwd()}/language_data'


language_2_ziplink: Optional[Dict[str, str]] = None
if language_2_ziplink is None:
    language_2_ziplink = scrape_language_2_downloadlink_dict()


def fetch_sentence_data_file(language: str):
    """ downloads and unzips respective sentence data file """

    zip_file_path = _download_sentence_data(language)
    _unzip_sentence_data(zip_file_path)


def fetch_all_available_sentence_data_files():
    locally_available_language_files: List[str] = os.listdir(_BASE_SAVE_DESTINATION_DIR_PATH)

    n_downloaded_language_files = 0
    for language in language_2_ziplink.keys():
        if language not in locally_available_language_files:
            fetch_sentence_data_file(language)
            n_downloaded_language_files += 1

    logging.info(f'Downloaded {n_downloaded_language_files} language files')


def _download_sentence_data(language: str) -> str:
    """
        Returns:
            absolute zip file save destination path """

    assert language_2_ziplink is not None

    download_link = f'{SENTENCE_DATA_PAGE_URL}/{language_2_ziplink[language]}'
    save_destination_dir = f'{_BASE_SAVE_DESTINATION_DIR_PATH}/{language}'
    if not os.path.exists(save_destination_dir):
        os.makedirs(save_destination_dir)

    save_destination_link = os.path.join(save_destination_dir, f'{language}.zip')
    patched_urllib._urlopener.retrieve(download_link, save_destination_link)  # type: ignore
    logging.info(f'Downloaded {language} sentence data')
    return save_destination_link


def _unzip_sentence_data(zip_file_link: str):
    """ unpacks zip file
        removes _about.txt
        renames sentence data text file """

    language_dir_path = zip_file_link[:zip_file_link.rfind(os.sep)]

    with zipfile.ZipFile(zip_file_link, 'r') as zip_ref:
        zip_ref.extractall(language_dir_path)

    # remove unpacked zip file, about.txt
    os.remove(zip_file_link)
    os.remove(f'{language_dir_path}/_about.txt')

    # rename sentence data file
    os.rename(f'{language_dir_path}/{os.listdir(language_dir_path)[0]}', f'{language_dir_path}/sentence_data.txt')
