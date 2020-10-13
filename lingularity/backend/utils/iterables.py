from typing import Set, Iterable, Any, List, Tuple
from itertools import tee, islice


def none_stripped(iterable: Iterable[Any]) -> List[Any]:
    return list(filter(lambda el: el is not None, iterable))


def iterables_intersection(sets: Iterable[Set[Any]]) -> Set[Any]:
    return set.intersection(*sets)


def windowed(iterable: Iterable[Any], n: int) -> Iterable[Tuple[Any]]:
    return zip(*(islice(vert_iterable, i, None) for i, vert_iterable in enumerate(tee(iterable, n))))


def longest_value(iterable: Iterable[Any]) -> Any:
    return sorted(iterable, key=len, reverse=True)[0]


def unzip(nested_list: Iterable[Iterable[Any]]):
    return zip(*nested_list)
