from typing import Callable, Iterable, TypeVar


_T = TypeVar('_T')


def first(iterable: Iterable[_T], key: Callable[[_T], bool]) -> _T:
    for x in iterable:
        if key(x):
            return x
    raise AttributeError