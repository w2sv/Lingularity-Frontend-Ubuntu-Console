from typing import Hashable, Union, Iterable, Any, Optional, List
from abc import ABC, abstractmethod


class UpsertDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*list(filter(lambda arg: arg is not None, args)), **kwargs)

    def upsert(self, key: Hashable, value: Union[Iterable[Any], Any]):
        if len(self):
            assert hasattr(self[next(iter(self.keys()))], '__iter__')

        iterable_value = hasattr(value, '__iter__')
        if key in self:
            self[key].append(value) if not iterable_value else self[key].extend(value)
        else:
            self[key] = [value] if not iterable_value else value


class Token2SentenceIndicesMap(ABC, UpsertDict):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def get_comprising_sentence_indices(self, entry: str) -> Optional[List[int]]:
        pass
