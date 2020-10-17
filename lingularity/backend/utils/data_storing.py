from typing import Any
import json
import sys
import pickle


def load_json(file_path: str):
    # abort loading when triggered during mining commencement
    if 'Mine' in sys.argv:
        return {}
    return json.load(open(f'{file_path}.json', 'r', encoding='utf-8'))


def write_pickle(data: Any, file_path: str):
    with open(file_path, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_pickle(file_path: str) -> Any:
    return pickle.load(open(file_path, 'rb'))
