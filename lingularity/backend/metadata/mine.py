from typing import Dict, Any, Callable, List, Optional
import json
from collections import defaultdict, OrderedDict
from functools import partial

from tqdm import tqdm

from . import METADATA_DIR_PATH

from lingularity.backend.trainers.base.forename_conversion import DEFAULT_FORENAMES
from lingularity.backend.metadata.types import LanguageMetadata, CountryMetadata
from lingularity.backend.trainers.base import SentenceData
from lingularity.backend.ops.data_mining.scraping import (scrape_sentence_data_download_links,
                                                          scrape_countries_language_employed_in,
                                                          scrape_popular_forenames, scrape_demonym)
from lingularity.backend.ops.google.translation import google_translator
from lingularity.backend.utils.strings import replace_multiple


def _save_as_json(data: Dict[Any, Any], file_name: str):
    with open(f'{METADATA_DIR_PATH}/{file_name}.json', 'w', encoding='utf-8') as write_file:
        json.dump(data, write_file, ensure_ascii=False, indent=4)


def _mine_metadata():
    language_2_download_link = scrape_sentence_data_download_links()

    for language, download_link in (progress_bar := tqdm(language_2_download_link.items(), total=len(language_2_download_link))):
        progress_bar.set_description(f'Mining {language} metadata', refresh=True)

        language_sub_dict = language_metadata[language]

        # set sentence data download links
        language_sub_dict['sentenceDataDownloadLinks'] = defaultdict(lambda: {})
        language_sub_dict['sentenceDataDownloadLinks']['tatoebaProject'] = download_link

        # set generic properties
        sentence_data = SentenceData(language)

        language_sub_dict['properties'] = {}
        language_sub_dict['properties']['isAgglutinative'] = False
        language_sub_dict['properties']['usesLatinScript'] = sentence_data.foreign_language_sentences.uses_latin_script

        _mine_and_set_forename_conversion_data(language)
        _mine_and_set_translations(language, sentence_data=sentence_data)


def _mine_and_set_forename_conversion_data(language: str):
    language_metadata[language]['countriesEmployedIn'] = []

    try:
        if (countries_language_employed_in := scrape_countries_language_employed_in(language)) is not None:
            for country in countries_language_employed_in:
                language_metadata[language]['countriesEmployedIn'].append(country)

                if country_metadata.get(country, 'nil') == 'nil':
                    if forename_conversion_data := scrape_popular_forenames(country):
                        forename_conversion_data['demonym'] = scrape_demonym(country)
                        country_metadata[country] = forename_conversion_data
                    else:
                        country_metadata[country] = None

    except ConnectionError as e:
        print(f'Obtained {e} when trying to scrape countries {language} employed in')


def _mine_and_set_translations(language: str, sentence_data: SentenceData):
    FORENAME_PLACEHOLDER = '{}'

    translation_sub_dict = {}

    if google_translator.is_available_for(language):
        translate = partial(google_translator.translate, src='English', dest=language)

        # lets go
        translation_sub_dict["letsGo"] = translate("Let's go!")

        # default forenames
        translation_sub_dict["defaultForenames"] = _get_default_forename_translations(sentence_data, translation_function=translate)

        # constitution query
        constitution_queries = map(translate, [f"How are you {DEFAULT_FORENAMES[0]}?", f"What's up {DEFAULT_FORENAMES[0]}?"])
        translation_sub_dict["constitutionQuery"] = list(map(lambda query: replace_multiple(query, strings=[forename_transcriptions[0], DEFAULT_FORENAMES[0]], replacement=FORENAME_PLACEHOLDER), constitution_queries))

    language_metadata[language]['translations'] = translation_sub_dict


def _get_default_forename_translations(sentence_data: SentenceData, translation_function: Callable) -> List[Optional[str]]:
    translations: List[Optional[str]] = []

    for forename_index, default_forename in enumerate(DEFAULT_FORENAMES):
        default_forename_translation = None

        if sentence_data.foreign_language_sentences.uses_latin_script and sentence_data.foreign_language_sentences.comprises_tokens(query_tokens=[default_forename]):
            default_forename_translation = default_forename

        elif sentence_data.foreign_language_sentences.comprises_tokens([google_translation := translation_function(default_forename)]):
            default_forename_translation = google_translation

        elif sentence_data_translation := sentence_data.deduce_forename_translations(default_forename) is not None:
            default_forename_translation = sentence_data_translation

        translations.append(default_forename_translation)

    return translations


if __name__ == '__main__':
    language_metadata: LanguageMetadata = defaultdict(lambda: {})
    country_metadata: CountryMetadata = {}

    _mine_metadata()

    # sort country metadata for legibility
    country_metadata = OrderedDict(sorted(country_metadata.items()))

    _save_as_json(language_metadata, file_name='languages')
    _save_as_json(country_metadata, file_name='countries')
