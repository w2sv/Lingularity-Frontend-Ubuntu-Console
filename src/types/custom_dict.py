from typing import Any, Hashable, Iterable, Union, Dict


class CustomDict(dict):
    def __init__(self, *args, **kwargs):
        args = list(filter(lambda arg: arg is not None, args))
        super().__init__(*args, **kwargs)

    def append_or_insert(self, key: Hashable, value: Union[Iterable[Any], Any]):
        """ assuming iterable values """

        iterable_value = hasattr(value, '__iter__')
        if key in self:
            self[key].append(value) if not iterable_value else self[key].extend(value)
        else:
            self[key] = [value] if not iterable_value else value
