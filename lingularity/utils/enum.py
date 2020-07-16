from enum import Enum


class ExtendedEnum(Enum):
    @classmethod
    def values(cls):
        return list(map(lambda element: element.value, cls))
