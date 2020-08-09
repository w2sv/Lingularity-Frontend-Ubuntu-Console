from typing import Any, Hashable, Iterable, Union


class CustomDict(dict):
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
