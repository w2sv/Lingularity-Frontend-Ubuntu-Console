from typing import Dict

from mypy_extensions import TypedDict


class LastSessionStatistics(TypedDict):
    trainer: str
    nFacedItems: int
    date: str
    language: str


TrainingChronic = Dict[str, Dict[str, int]]
