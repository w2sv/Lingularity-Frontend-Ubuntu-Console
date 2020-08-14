from mypy_extensions import TypedDict


class LastSessionStatistics(TypedDict):
    trainer: str
    nFacedItems: int
    date: str
    language: str


class VocableAttributes(TypedDict):
    t: str
    tf: int
    s: float
    lfd: str
