from abc import ABC, abstractmethod
from typing import List, Type, Dict

from termcolor import colored

from lingularity.backend.utils.iterables import unzip
from lingularity.frontend.console.utils.output import align


class TrainingOption(ABC):
    _FRONTEND_INSTANCE = None

    _ALLOWED_VARIABLE_NAMES = ('keyword', 'explanation')

    @staticmethod
    @abstractmethod
    def set_frontend_instance(instance):
        pass

    def __init__(self, keyword: str, explanation: str):
        self.keyword = keyword
        self.explanation = explanation

    @abstractmethod
    def execute(self):
        pass

    def __setattr__(self, key, value):
        if key in TrainingOption.__dict__['_ALLOWED_VARIABLE_NAMES']:
            self.__dict__[key] = value

        else:
            assert hasattr(self._FRONTEND_INSTANCE, key)

            setattr(self._FRONTEND_INSTANCE, key, value)

    def __getattr__(self, item):
        return getattr(self._FRONTEND_INSTANCE, item)


class TrainingOptions(dict):
    RawType = Dict[str, TrainingOption]

    def __init__(self, option_classes: List[Type[TrainingOption]]):
        super().__init__({option.keyword: option for option in [cls() for cls in option_classes]})  # type: ignore

        self.keywords: List[str] = [option.keyword for option in self.values()]
        self.instructions: List[str] = self._compose_instruction()

    def _compose_instruction(self) -> List[str]:
        return align(*unzip(map(lambda option: (colored(option.keyword, 'red'), f'to {option.explanation}'), self.values())))
