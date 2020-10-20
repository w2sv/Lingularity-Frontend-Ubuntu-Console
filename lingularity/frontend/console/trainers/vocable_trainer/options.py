__all__ = ['VocableTrainerOption', 'AddVocable', 'AlterLatestCreatedVocableEntry',
           'AlterLatestFacedVocableEntry', 'Exit']

from abc import ABC
from time import sleep

from lingularity.frontend.console.utils.terminal import centered_print, erase_lines
from lingularity.frontend.console.trainers.base.options import TrainingOption


class VocableTrainerOption(TrainingOption, ABC):
    _FRONTEND_INSTANCE = None

    @staticmethod
    def set_frontend_instance(instance):
        VocableTrainerOption._FRONTEND_INSTANCE = instance

    def __init__(self, keyword: str, explanation: str):
        super().__init__(keyword, explanation)


class AddVocable(VocableTrainerOption):
    def __init__(self):
        super().__init__('#vocable', 'add a new vocable')

    def execute(self):
        n_printed_lines = self._get_new_vocable()
        erase_lines(n_printed_lines + 1)


class VocableModifier(VocableTrainerOption, ABC):
    def _modify_vocable_entry(self, vocable_entry, message: str):
        if vocable_entry is None:
            centered_print(message)
            sleep(1.5)
            erase_lines(2)
        else:
            n_printed_lines = self._alter_vocable_entry(vocable_entry)
            erase_lines(n_printed_lines)


class AlterLatestFacedVocableEntry(VocableModifier):
    def __init__(self):
        super().__init__('#faced', 'alter the most recently FACED vocable entry')

    def execute(self):
        self._modify_vocable_entry(self._latest_faced_vocable_entry, "Seriously?")


class AlterLatestCreatedVocableEntry(VocableModifier):
    def __init__(self):
        super().__init__('#added', 'alter the most recently ADDED vocable entry')

    def execute(self):
        self._modify_vocable_entry(self._latest_created_vocable_entry, "You haven't added any vocable during the current session")


class Exit(VocableTrainerOption):
    def __init__(self):
        super().__init__('#exit', 'terminate program\n')

    def execute(self):
        erase_lines(1)
