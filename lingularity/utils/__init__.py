from typing import Optional, Any


def either(value: Optional[Any], default: Any) -> Any:
    return [value, default][value is None]
