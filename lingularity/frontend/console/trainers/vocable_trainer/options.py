__all__ = ['AlterCurrentVocableEntry', 'DeleteVocableEntry']

from lingularity.frontend.console.utils import input_resolution, output
from lingularity.frontend.console.trainers.base.options import TrainingOption


class AlterCurrentVocableEntry(TrainingOption):
    def __init__(self):
        self.keyword, self.explanation = 'alter', "alter the current vocable"

    def __call__(self):
        n_printed_lines = self._alter_vocable_entry(self._current_vocable_entry)
        output.erase_lines(n_printed_lines - 1)


class DeleteVocableEntry(TrainingOption):
    def __init__(self):
        self.keyword, self.explanation = 'delete', "delete the current vocable entry"

    def __call__(self):
        output.centered_print(f"\nAre you sure you want to irreversibly delete {str(self._current_vocable_entry)}? (y)es/(n)o")

        if input_resolution.query_relentlessly(output.centered_print_indentation(' '), ['yes', 'no']) == 'yes':
            self._backend.mongodb_client.delete_vocable_entry(self._current_vocable_entry.as_dict)
        output.erase_lines(3)
