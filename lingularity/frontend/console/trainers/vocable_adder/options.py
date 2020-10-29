__all__ = ['AlterLatestCreatedVocableEntry', 'Exit']

from abc import ABC
from time import sleep

from lingularity.frontend.console.utils import output
from lingularity.frontend.console.trainers.base.options import TrainingOption


class VocableAdderOption(TrainingOption, ABC):
    _FRONTEND_INSTANCE = None

    @staticmethod
    def set_frontend_instance(instance):
        VocableAdderOption._FRONTEND_INSTANCE = instance


class AlterLatestCreatedVocableEntry(VocableAdderOption):
    def __init__(self):
        self.keyword, self.explanation = 'wait', "rectify the vocable entry you've just added"

    def __call__(self):
        n_printed_lines = self._alter_vocable_entry(self._latest_created_vocable_entry)
        output.erase_lines(n_printed_lines - 1)


class Exit(VocableAdderOption):
    def __init__(self):
        self.keyword, self.explanation = 'quit', 'return to training selection screen'

    def __call__(self):
        output.erase_lines(1)
