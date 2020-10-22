from abc import ABC, abstractmethod
from typing import List, Type, Dict, Iterator

from termcolor import colored

from lingularity.backend.utils.iterables import unzip
from lingularity.frontend.console.utils.terminal import tabulate


class TrainingOption(ABC):
    _FRONTEND_INSTANCE = None

    _VARIABLE_NAMES = ('keyword', '_explanation')

    @staticmethod
    @abstractmethod
    def set_frontend_instance(instance):
        pass

    def __init__(self, keyword: str, explanation: str):
        self.keyword = keyword
        self._explanation = explanation

    @property
    def instruction(self) -> str:
        return f"\t  {colored(self.keyword, 'red')} to {self._explanation}"

    @abstractmethod
    def execute(self):
        pass

    def __setattr__(self, key, value):
        if key in TrainingOption.__dict__['_VARIABLE_NAMES']:
            self.__dict__[key] = value

        else:
            assert hasattr(self._FRONTEND_INSTANCE, key)

            setattr(self._FRONTEND_INSTANCE, key, value)

    def __getattr__(self, item):
        return getattr(self._FRONTEND_INSTANCE, item)


class TrainingOptions:
    def __init__(self, option_classes: List[Type[TrainingOption]]):
        options = [cls() for cls in option_classes]  # type: ignore

        self.keywords: List[str] = [option.keyword for option in options]
        self.instructions = self._
        self._keyword_2_option: Dict[str, TrainingOption] = {option.keyword: option for option in options}

    def __getitem__(self, item: str) -> TrainingOption:
        return self._keyword_2_option[item]
