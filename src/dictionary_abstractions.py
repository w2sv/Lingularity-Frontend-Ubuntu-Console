from typing import Iterable, Tuple, Optional, AbstractSet, ValuesView, Any, Union, Dict
from abc import ABC, abstractmethod
from collections.abc import MutableMapping


class CustomDict(MutableMapping, ABC):
    def __init__(self, mapping_data: Optional[MutableMapping] = None):
        self.mapping = {}
        self.update(mapping_data)

    def __getitem__(self, key):
        return self.mapping[key]

    def __setitem__(self, key, value):
        self.mapping[key] = value

    def __delitem__(self, key):
        del self.mapping[key]

    def __iter__(self):
        return iter(self.mapping)

    def __len__(self):
        return len(self.mapping)

    def __str__(self):
        return str(self.mapping)

    def items(self) -> AbstractSet[Tuple[Any, Any]]:
        return self.mapping.items()

    def keys(self) -> AbstractSet[Any]:
        return self.mapping.keys()

    def values(self) -> ValuesView[Any]:
        return self.mapping.values()


class IterableKeyDict(CustomDict):
    def __init__(self, mapping_data: Optional[MutableMapping] = None):
        super().__init__(mapping_data)

    def append_or_insert(self, key: Any, value: Union[Iterable[Any], Any]):
        if key in self:
            self[key].append(value) if not hasattr('__iter__', value) else self[key].extend(value)
        else:
            self[key] = [value] if not hasattr('__iter__', value) else value


class FrozenIterableKeyDict(IterableKeyDict):
    def __init__(self, mapping_data: Optional[Dict[Any, Any]] = None):
        super().__init__(mapping_data)
        self.hash = None

    def __hash__(self):
        if self.hash is None:
            _hash = 0
            for pair in self.items():
                _hash ^= hash(pair)
            self.hash = _hash
        return self.hash


if __name__ == '__main__':
    frozen_dict = FrozenIterableKeyDict({4: 7, 9: 3})
    print(frozen_dict.__hash__())
