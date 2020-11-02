from typing import *
import os

from termcolor import colored
from tqdm import tqdm

from .foundations import token_maps_foundations
from lingularity.backend.metadata import language_metadata
from lingularity.backend.utils import data, string_resources
from lingularity.backend.trainers.components.sentence_data import SentenceData
from lingularity.backend.trainers.components.mappings.token.sentence_indices import (
    get_token_sentence_indices_map,
    LemmaSentenceIndicesMap,
    TokenSentenceIndicesMap
)
from lingularity.backend.trainers.components.mappings.token.occurrences import (
    TokenOccurrencesMap,
    create_token_occurrences_map
)


assert __name__ == '__main__', 'module solely to be invoked as main'


def create_token_maps(language: str) -> Tuple[TokenSentenceIndicesMap, TokenOccurrencesMap]:
    sentence_data = SentenceData(language=language)

    token_sentence_indices_map = get_token_sentence_indices_map(language=language)

    # procure token maps foundations
    sentence_indices_map_foundation, occurrence_map_foundations = token_maps_foundations(
        sentence_data=sentence_data,
        tokenize_with_pos_tags=token_sentence_indices_map.tokenize_with_pos_tags
    )

    # create token maps
    token_sentence_indices_map.create(sentence_index_2_unique_tokens=sentence_indices_map_foundation)
    token_occurrences_map = create_token_occurrences_map(
        paraphrases_tokens_list=occurrence_map_foundations[0],
        paraphrases_pos_tags_list=[None, occurrence_map_foundations[1]][type(token_sentence_indices_map) is LemmaSentenceIndicesMap]
    )

    return token_sentence_indices_map, token_occurrences_map


def __call__():
    SAVE_DIR = f'{os.getcwd()}/lingularity/backend/data/token-maps'

    for language in (progress_bar := tqdm(language_metadata.keys(), total=len(language_metadata))):
        if language not in os.listdir(SAVE_DIR) and language != string_resources.ENGLISH:
            progress_bar.set_description(f'Creating {colored(language, "red")} maps...', refresh=True)

            # create maps
            token_sentence_indices_map, token_occurrences_map = create_token_maps(language=language)

            # create language-specific subdir
            language_dir = f'{SAVE_DIR}/{language}'
            os.mkdir(language_dir)

            # save maps
            data.write_pickle(token_sentence_indices_map.data, file_path=f'{language_dir}/sentence-indices-map')
            data.write_pickle(token_occurrences_map.data, file_path=f'{language_dir}/occurrences-map')


__call__()
