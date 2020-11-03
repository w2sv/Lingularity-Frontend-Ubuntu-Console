from typing import Optional, Any


def either(value: Optional[Any], default: Any) -> Any:
    """ Returns:
            value if != None, else default """

    return [value, default][value is None]
