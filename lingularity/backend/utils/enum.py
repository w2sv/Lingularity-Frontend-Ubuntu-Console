from typing import List, Any
from enum import Enum


class ExtendedEnum(Enum):
    @classmethod
    def names(cls) -> List[str]:
        return list(map(lambda element: element.name, cls))  # type: ignore

    @classmethod
    def values(cls) -> List[Any]:
        return list(map(lambda element: element.value, cls))
