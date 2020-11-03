from typing import Mapping, Any
import collections
from abc import ABC
from functools import wraps

from lingularity.backend import TOKEN_MAPS_PATH
from lingularity.backend.utils import data, strings


class CustomMapping(ABC, collections.abc.Mapping):
    _Type = Mapping[Any, Any]

    def __init_subclass__(cls):
        if CustomMapping._Type is cls._Type:
            raise NotImplementedError("CustomMapping subclass required to override _Type")

    @property
    def data_file_name(self) -> str:
        """ Returns:
                lowercase, dash-joined class name without 'token' """

        return '-'.join(map(lambda string: string.lower(), strings.split_at_uppercase(self.__class__.__name__)[1:]))

    def _data(self, language: str, create: bool) -> _Type:
        return {} if create else self._load_data(language=language)

    def _load_data(self, language: str) -> _Type:
        return data.load_pickle(file_path=f'{TOKEN_MAPS_PATH}/{language}/{self.data_file_name}')

    @property
    def data(self) -> _Type:
        return {**self}


def _display_creation_kickoff_message(message: str):
    def wrapper(func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            if '{}' in message:
                print(message.format(args[0].data_file_name))
            else:
                print(message)

            return func(*args, **kwargs)
        return func_wrapper
    return wrapper
