from dataclasses import dataclass


@dataclass(frozen=True)
class SequencePlotData:
    sequence: list[float]
    dates: list[str]
    item_name: str
