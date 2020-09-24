from typing import Set, Iterable, Any, Sequence, List


def none_stripped(iterable: Iterable[Any]) -> List[Any]:
    return list(filter(lambda el: el is not None, iterable))


def iterables_intersection(nested_iterables: Sequence[Iterable[Any]]) -> Set[Any]:
    if type(nested_iterables[0]) is not set:
        nested_iterables = list(map(set, nested_iterables))
    return set.intersection(*nested_iterables)  # type: ignore
