from typing import List, Dict, Any


def append_2_or_insert_key(map: Dict[Any, List[Any]], key: Any, value: Any) -> None:
    if map.get(key) is None:
        map[key] = [value]
    else:
        map[key].append(value)