from time import sleep

from frontend.utils import output
from frontend.trainers.base.options import TrainingOption


class Exit(TrainingOption):
    def __init__(self):
        self.keyword, self.explanation = 'quit', 'return to training selection screen'

    def __call__(self):
        TrainingOption.exit_training = True


class RectifyLatestAddedVocableEntry(TrainingOption):
    def __init__(self):
        self.keyword, self.explanation = 'wait', "rectify the vocable entry you've just added"

    def __call__(self):
        if self._latest_created_vocable_entry is None:
            output.centered_print("YOU HAVEN'T ADDED ANY VOCABLE ENTRY DURING THE CURRENT SESSION")
            sleep(1.5)
            output.erase_lines(2)
        else:
            n_printed_lines = self._alter_vocable_entry(self._latest_created_vocable_entry)
            output.erase_lines(n_printed_lines)


class AddVocable(TrainingOption):
    def __init__(self):
        self.keyword, self.explanation = 'new', 'add a new vocable'

    def __call__(self):
        n_printed_lines = self._add_vocable()
        output.erase_lines(n_printed_lines + 1)
