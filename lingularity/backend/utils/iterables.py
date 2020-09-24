from typing import Set, Iterable, Any, List


def none_stripped(iterable: Iterable[Any]) -> List[Any]:
    return list(filter(lambda el: el is not None, iterable))


def iterables_intersection(nested_iterables: Iterable[Set[Any]]) -> Set[Any]:
    return set.intersection(*nested_iterables)
