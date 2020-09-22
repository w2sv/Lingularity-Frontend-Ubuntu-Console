from typing import Hashable, Union, Iterable, Any, Optional, List
from abc import ABC, abstractmethod


class Token2SentenceIndicesMap(ABC):
    def __init__(self, _map):
        self._map = _map

    @abstractmethod
    def get_comprising_sentence_indices(self, entry: str) -> Optional[List[int]]:
        pass

    def __getattr__(self, item):
        return getattr(self._map, item)

    def __getitem__(self, item):
        return self._map[item]

    def __setitem__(self, item, value):
        self._map[item] = value

    def __str__(self):
        return str(self._map)
