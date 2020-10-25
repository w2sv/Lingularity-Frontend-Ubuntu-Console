from typing import Dict, Optional

from mypy_extensions import TypedDict


class LastSessionStatistics(TypedDict):
    trainer: str
    nFacedItems: int
    date: str
    language: str


class VocableData(TypedDict):
    t: str
    tf: int
    s: float
    lfd: Optional[str]


TrainingChronic = Dict[str, Dict[str, int]]
