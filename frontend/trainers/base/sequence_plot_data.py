from typing import List
from dataclasses import dataclass


@dataclass(frozen=True)
class SequencePlotData:
    sequence: List[float]
    dates: List[str]
    item_name: str
