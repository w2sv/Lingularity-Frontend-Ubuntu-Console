import os

from backend.utils import io


_BASE_PATH = f'{os.getcwd()}/frontend/data'
COUNTRY_METADATA_PATH = f'{_BASE_PATH}/country-metadata'
MAIN_COUNTRY_DATA_PATH = f'{_BASE_PATH}/main-countries'


country_metadata = io.load_json(COUNTRY_METADATA_PATH)
_main_country_data = io.load_json(MAIN_COUNTRY_DATA_PATH)


def main_country_flag(language: str) -> str:
    return country_metadata[_main_country_data[language]]['flag']
