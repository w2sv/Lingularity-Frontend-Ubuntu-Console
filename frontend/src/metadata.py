from backend.src.utils import io
from frontend.src.paths import DATA_DIR_PATH


COUNTRY_METADATA_PATH = DATA_DIR_PATH / 'country-metadata.json'
MAIN_COUNTRY_DATA_PATH = DATA_DIR_PATH / 'main-countries.json'

country_metadata = io.load_json(COUNTRY_METADATA_PATH)


def main_country_flag(language: str) -> str:
    return country_metadata[_main_country_data[language]]['flag']


_main_country_data = io.load_json(MAIN_COUNTRY_DATA_PATH)
