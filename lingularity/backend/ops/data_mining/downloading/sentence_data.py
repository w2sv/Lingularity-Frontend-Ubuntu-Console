from typing import List
import os
import warnings
import logging
import zipfile

from lingularity.backend.ops.data_mining.scraping.sentence_data_download_links import SENTENCE_DATA_PAGE_URL, scrape_sentence_data_download_links
from .utils import patched_urllib

warnings.filterwarnings('ignore')


_BASE_SAVE_DESTINATION_DIR_PATH = f'{os.getcwd()}/.language_data'


language_2_downloadlink = scrape_sentence_data_download_links()


def download_sentence_data(language: str):
    """ downloads and unzips respective sentence data file """

    print('Downloading sentence data...')
    zip_file_path = _download_sentence_data(language)
    _process_zip_file(zip_file_path)


# def fetch_all_available_sentence_data_files(source='tatoebaProject'):
#     locally_available_language_files: List[str] = os.listdir(_BASE_SAVE_DESTINATION_DIR_PATH)
#
#     n_downloaded_language_files = 0
#     for language, language_data in language_metadata.items():
#         if language not in locally_available_language_files:
#             download_sentence_data(language_data["sentenceDataDownloadLinks"][source])
#             n_downloaded_language_files += 1
#
#     logging.info(f'Downloaded {n_downloaded_language_files} language files')


def _download_sentence_data(language: str, source='tatoebaProject') -> str:
    """
        Returns:
            absolute zip file save destination path """

    download_link = f'{SENTENCE_DATA_PAGE_URL}/{language_2_downloadlink[language]}'
    save_destination_dir = f'{_BASE_SAVE_DESTINATION_DIR_PATH}/{language}'
    if not os.path.exists(save_destination_dir):
        os.makedirs(save_destination_dir)

    save_destination_link = os.path.join(save_destination_dir, f'{language}.zip')
    patched_urllib._urlopener.retrieve(download_link, save_destination_link)  # type: ignore
    logging.info(f'Downloaded {language} sentence data')
    return save_destination_link


def _process_zip_file(zip_file_link: str):
    """ - unpack zip file
        - remove _about.txt
        - strip reference appendices from sentence data file
        - rename sentence data file """

    language_dir_path = zip_file_link[:zip_file_link.rfind(os.sep)]

    with zipfile.ZipFile(zip_file_link, 'r') as zip_ref:
        zip_ref.extractall(language_dir_path)

    # remove unpacked zip file, about.txt
    os.remove(zip_file_link)
    os.remove(f'{language_dir_path}/_about.txt')

    sentence_data_file_path = f'{language_dir_path}/{os.listdir(language_dir_path)[0]}'

    # remove reference appendices from sentence data file
    raw_sentence_data = open(sentence_data_file_path, 'r', encoding='utf-8').readlines()
    processed_sentence_data = ('\t'.join(row.split('\t')[:2]) + '\n' for row in raw_sentence_data)
    with open(sentence_data_file_path, 'w', encoding='utf-8') as sentence_data_file:
        sentence_data_file.writelines(processed_sentence_data)

    os.rename(sentence_data_file_path, f'{language_dir_path}/sentence_data.txt')
