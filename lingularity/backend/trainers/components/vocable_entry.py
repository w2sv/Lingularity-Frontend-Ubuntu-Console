from typing import Optional, Dict
from functools import cached_property

from lingularity.backend.database.document_types import VocableData
from lingularity.backend.utils.date import n_days_ago


class VocableEntry:
    """ Vocable Entry abstraction providing additional properties as well as
    transformation capabilities """

    @classmethod
    def new(cls, vocable: str, translation: str):
        return cls(vocable, {
            't': translation,
            'tf': 0,
            's': 0.0,
            'lfd': None})

    def __init__(self, vocable: str, data: VocableData):
        self.vocable: str = vocable
        self._data: VocableData = data

    @property
    def as_dict(self) -> Dict[str, VocableData]:
        return {self.vocable: self._data}

    # ----------------
    # Vocable/Meaning
    # ----------------
    @property
    def meaning(self) -> str:
        return self._data['t']

    @cached_property
    def the_stripped_meaning(self):
        return self._data['t'].lstrip('the ')

    def __str__(self) -> str:
        """ Returns:
                dash joined line repr. i.e. '{vocable} - {meaning}' """

        return ' - '.join([self.vocable, self.meaning])

    def alter(self, new_vocable: str, new_meaning: str):
        self.vocable = new_vocable
        self._data['t'] = new_meaning

        try:
            del self.the_stripped_meaning
        except AttributeError:
            pass

    # ----------------
    # Last Faced Date
    # ----------------
    @property
    def last_faced_date(self) -> Optional[str]:
        return self._data['lfd']

    @property
    def is_new(self) -> bool:
        return self.last_faced_date is None

    # ----------------
    # Times Faced
    # ----------------
    @property
    def times_faced(self) -> int:
        return self._data['tf']

    def _increment_times_faced(self):
        self._data['tf'] += 1

    # ----------------
    # Score
    # ----------------
    @property
    def score(self) -> float:
        return self._data['s']

    def update_score(self, increment: float):
        self._data['s'] += increment
        self._increment_times_faced()

    # ----------------
    # Perfection
    # ----------------
    @property
    def perfected(self) -> bool:
        return self.is_perfected(self._data)

    @staticmethod
    def is_perfected(data: VocableData) -> bool:
        if data['lfd'] is None:
            return False
        return data['s'] >= 5 and n_days_ago(data['lfd']) < 50
