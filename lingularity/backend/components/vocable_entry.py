from typing import Dict, Any, Optional

from lingularity.backend.utils.date import n_days_ago


class VocableEntry:
    """ wrapper for vocable vocable_entry dictionary of structure
            {foreign_token: {tf: int},
                            {lfd: Optional[str]},
                            {s: float},
                            {t: str}}

        returned by mongodb, facilitating access to attributes, as well as
        providing additional convenience functionality """

    RawType = Dict[str, Dict[str, Any]]

    @classmethod
    def new(cls, vocable: str, translation: str):
        return cls(entry={vocable: {'tf': 0,
                              'lfd': None,
                              's': 0,
                              't': translation}}, reference_to_foreign=None)

    def __init__(self, entry: RawType, reference_to_foreign: Optional[bool]):
        self.entry = entry
        self._reference_to_foreign = reference_to_foreign

    def alter(self, new_vocable: str, new_translation: str):
        self.entry[self.token]['t'] = new_translation
        self.entry[new_vocable] = self.entry.pop(self.token)

    # -----------------
    # Token
    # -----------------
    @property
    def token(self) -> str:
        return next(iter(self.entry.keys()))

    @property
    def display_token(self) -> str:
        return self.translation if not self._reference_to_foreign else self.token

    # -----------------
    # Translation
    # -----------------
    @property
    def translation(self) -> str:
        return self.entry[self.token]['t']

    @property
    def display_translation(self) -> str:
        return self.translation if self._reference_to_foreign else self.token

    # -----------------
    # Additional properties
    # -----------------
    @property
    def last_faced_date(self) -> Optional[str]:
        return self.entry[self.token]['lfd']

    @property
    def score(self) -> float:
        return self.entry[self.token]['s']

    @score.setter
    def score(self, value):
        self.entry[self.token]['s'] = value

    def update_score(self, increment: float):
        self.score += increment

    @property
    def is_new(self) -> bool:
        return self.last_faced_date is None

    @property
    def line_repr(self) -> str:
        """ i.e. f'{token} - {translation}' """

        return ' - '.join([self.token, self.translation])

    @property
    def is_perfected(self) -> bool:
        if self.last_faced_date is None:
            return False
        return self.score >= 5 and n_days_ago(self.last_faced_date) < 50

    # -----------------
    # Dunder(s)
    # -----------------
    def __str__(self):
        return str(self.entry)
