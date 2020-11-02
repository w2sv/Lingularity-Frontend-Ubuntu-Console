from collections.abc import Mapping
from abc import ABC


class CustomMapping(ABC, Mapping):
    @property
    def data(self):
        return {**self}
