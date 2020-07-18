from typing import List
from enum import Enum


class ExtendedEnum(Enum):
    @classmethod
    def values(cls):
        return list(map(lambda element: element.value, cls))

    @classmethod
    def names(cls) -> List[str]:
        return list(map(lambda element: element.name, cls))
