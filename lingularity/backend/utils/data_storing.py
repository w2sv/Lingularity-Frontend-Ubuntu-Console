from typing import Any, Dict
import json
import sys
import pickle


def load_json(file_path: str):
    # abort loading when triggered during mining commencement
    if '-Mine' in sys.argv and 'correction' not in file_path:
        return {}

    with open(f'{file_path}.json', 'r', encoding='utf-8') as read_file:
        return json.load(read_file)


def write_json(data: Dict[Any, Any], file_path: str):
    with open(f'{file_path}.json', 'w', encoding='utf-8') as write_file:
        json.dump(data, write_file, ensure_ascii=False, indent=4)


def write_pickle(data: Any, file_path: str):
    with open(file_path, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_pickle(file_path: str) -> Any:
    return pickle.load(open(file_path, 'rb'))
