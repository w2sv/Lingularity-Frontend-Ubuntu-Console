""" https://spacy.io/models """

from typing import Any
import os

import spacy


Model = Any


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


def load_model(language: str) -> Model:
    model_name = _assemble_model_name(language=language)

    try:
        return _load_model(model_name=model_name)
    except OSError:
        _install_additional_dependencies_if_required(language=language)

        # try to download model
        if os.system(f'python -m spacy download {model_name}') == 256:
            raise EnvironmentError("Couldn't download spacy model")

    return _load_model(model_name=model_name)


def _assemble_model_name(language: str) -> str:
    MODEL_SIZE = 'sm'

    return f'{LANGUAGE_2_MODEL_IDENTIFIERS[language][0]}_core_{LANGUAGE_2_MODEL_IDENTIFIERS[language][1]}_{MODEL_SIZE}'


def _load_model(model_name: str):
    print('Loading model...')
    return spacy.load(model_name)


def _install_additional_dependencies_if_required(language: str):
    # TODO: test
    relative_os_dependency_installation_file_path = f'os_dependencies/languages/{language}.sh'
    if os.path.exists(f'{os.getcwd()}/{relative_os_dependency_installation_file_path}'):
        os.system(f'bash {relative_os_dependency_installation_file_path}')
