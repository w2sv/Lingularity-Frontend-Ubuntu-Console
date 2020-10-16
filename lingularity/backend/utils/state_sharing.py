from typing import Any, Dict
from abc import ABC


class MonoStatePossessor(ABC):
    _mono_state: Dict[str, Any] = {}

    def __init__(self):
        self.__dict__ = self._mono_state

    @classmethod
    def get_instance(cls):
        instance = cls.__new__(cls)
        super(cls, instance).__init__()
        return instance
