""" https://spacy.io/models """

from typing import Any
import os
from enum import Enum, auto

import spacy


Model = Any


def load_model(language: str) -> Model:
    print('Loading model...')
    return spacy.load(_assemble_model_name(language=language))


# ---------------
# POS Values
# ---------------
class PosValue(Enum):
    Null = 0
    Low = auto()
    Medium = auto()
    High = auto()


POS_VALUES = {
    'NOUN': PosValue.High, 'VERB': PosValue.High, 'ADJ': PosValue.High, 'ADV': PosValue.High,
    'NUM': PosValue.Medium,
    'AUX': PosValue.Low, 'ADP': PosValue.Low, 'PRON': PosValue.Low
}


# ---------------
# Model Name Assembly
# ---------------
_WEB, _NEWS = 'web', 'news'


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

def _assemble_model_name(language: str) -> str:
    MODEL_SIZE_IDENTIFIER = 'md'

    return f'{LANGUAGE_2_MODEL_IDENTIFIERS[language][0]}_core_{LANGUAGE_2_MODEL_IDENTIFIERS[language][1]}_{MODEL_SIZE_IDENTIFIER}'


ELIGIBLE_LANGUAGES = set(LANGUAGE_2_MODEL_IDENTIFIERS.keys())


if __name__ == '__main__':
    """ Download all available spacy models alongside additional dependencies """


    def download_models():
        for language in LANGUAGE_2_MODEL_IDENTIFIERS.keys():
            os.system(f'python -m spacy download {_assemble_model_name(language=language)}')
            _install_os_dependencies_if_required(language)


    def _install_os_dependencies_if_required(language: str):
        relative_os_dependency_installation_file_path = f'os-dependencies/languages/{language}.sh'

        if os.path.exists(f'{os.getcwd()}/{relative_os_dependency_installation_file_path}'):
            os.system(f'bash {relative_os_dependency_installation_file_path}')


    def install_additional_dependencies():
        ADDITIONAL_DEPENDENCIES = [
            'sudachipy sudachidict_core',
            'jieba'
        ]

        for dependency in ADDITIONAL_DEPENDENCIES:
            os.system(f'pip install {dependency}')

    download_models()
    install_additional_dependencies()
