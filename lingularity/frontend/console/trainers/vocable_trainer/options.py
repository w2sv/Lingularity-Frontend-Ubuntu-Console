__all__ = ['VocableTrainerOption', 'AddVocable', 'AlterLatestCreatedVocableEntry',
           'AlterCurrentVocableEntry', 'Exit', 'DeleteVocableEntry']

from abc import ABC
from time import sleep

from lingularity.frontend.console.utils import input_resolution, output
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
        super().__init__('new', 'add a new vocable')

    def execute(self):
        n_printed_lines = self._add_vocable()
        output.erase_lines(n_printed_lines + 1)


class AlterLatestCreatedVocableEntry(VocableTrainerOption):
    def __init__(self):
        super().__init__('wait', "rectify the vocable entry you've just added")

    def execute(self):
        if self._latest_created_vocable_entry is None:
            output.centered_print("YOU HAVEN'T ADDED ANY ENTRY DURING THE CURRENT SESSION")
            sleep(1.5)
            output.erase_lines(1)

        n_printed_lines = self._alter_vocable_entry(self._latest_created_vocable_entry)
        output.erase_lines(n_printed_lines - 1)


class AlterCurrentVocableEntry(VocableTrainerOption):
    def __init__(self):
        super().__init__('alter', "alter the current vocable")

    def execute(self):
        n_printed_lines = self._alter_vocable_entry(self._current_vocable_entry)
        output.erase_lines(n_printed_lines - 1)


class DeleteVocableEntry(VocableTrainerOption):
    def __init__(self):
        super().__init__('delete', "delete the current vocable entry")

    def execute(self):
        output.centered_print(f"\nAre you sure you want to irreversibly delete {str(self._current_vocable_entry)}? (y)es/(n)o")

        if input_resolution.query_relentlessly(output.centered_print_indentation(' '), ['yes', 'no']) == 'yes':
            self._backend.mongodb_client.delete_vocable_entry(self._current_vocable_entry)
        output.erase_lines(3)


class Exit(VocableTrainerOption):
    def __init__(self):
        super().__init__('exit', 'exit training')

    def execute(self):
        output.erase_lines(1)
