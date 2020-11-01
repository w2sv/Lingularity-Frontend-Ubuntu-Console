""" https://spacy.io/models """

from typing import Any
import os

import spacy


Model = Any
Token = spacy.tokens.Token


POS_VALUES = {
    'NOUN': 5, 'VERB': 5, 'ADJ': 5, 'ADV': 5,
    'NUM': 4,
    'AUX': 3, 'ADP': 3, 'PRON': 3
}


_WEB = 'web'
_NEWS = 'news'


LANGUAGE_2_MODEL_IDENTIFIERS = {
    'Chinese': ['zh', _WEB],
    'Danish': ['da', _NEWS],
    'Dutch': ['nl', _NEWS],
    'English': ['en', _WEB],
    'French': ['fr', _NEWS],
    'German': ['de', _NEWS],
    'Greek': ['el', _NEWS],
    'Italian': ['it', _NEWS],
    'Japanese': ['ja', _NEWS],
    'Lithuanian': ['lt', _NEWS],
    'Norwegian': ['nb', _NEWS],
    'Polish': ['pl', _NEWS],
    'Portuguese': ['pt', _NEWS],
    'Romanian': ['ro', _NEWS],
    'Spanish': ['es', _NEWS]
}

ELIGIBLE_LANGUAGES = set(LANGUAGE_2_MODEL_IDENTIFIERS.keys())


def load_model(language: str):
    print('Loading model...')
    return spacy.load(_assemble_model_name(language=language))


def _assemble_model_name(language: str) -> str:
    MODEL_SIZE_IDENTIFIER = 'md'

    return f'{LANGUAGE_2_MODEL_IDENTIFIERS[language][0]}_core_{LANGUAGE_2_MODEL_IDENTIFIERS[language][1]}_{MODEL_SIZE_IDENTIFIER}'


if __name__ == '__main__':
    def download_models():
        for language in LANGUAGE_2_MODEL_IDENTIFIERS.keys():
            os.system(f'python -m spacy download {_assemble_model_name(language=language)}')
            _install_os_dependencies_if_required(language)


    def _install_os_dependencies_if_required(language: str):
        relative_os_dependency_installation_file_path = f'os-dependencies/languages/{language}.sh'

        if os.path.exists(f'{os.getcwd()}/{relative_os_dependency_installation_file_path}'):
            os.system(f'bash {relative_os_dependency_installation_file_path}')

    download_models()
