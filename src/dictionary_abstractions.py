from typing import Iterable, Tuple, Optional, AbstractSet, ValuesView, Any, Union, Dict, Hashable
from collections.abc import MutableMapping


class CustomDict(MutableMapping):
    def __init__(self, mapping_data: Optional[Dict[Hashable, Any]] = None):
        self.mapping = {}
        if mapping_data is not None:
            self.update(mapping_data)

    def append_or_insert(self, key: Hashable, value: Any):
        """ assuming iterable keys """
        if key in self:
            self[key].append(value) if not hasattr(value, '__iter__') else self[key].extend(value)
        else:
            self[key] = [value] if not hasattr(value, '__iter__') else value

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


if __name__ == '__main__':
    dic = CustomDict({4: 8, 9: 5})
    print(dic)