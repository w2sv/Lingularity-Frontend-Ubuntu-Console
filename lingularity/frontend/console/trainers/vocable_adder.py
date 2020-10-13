from typing import Optional
from enum import Enum

import cursor

from lingularity.backend.trainers import VocableAdderBackend
from lingularity.backend.database import MongoDBClient
from lingularity.frontend.console.trainers import VocableTrainerConsoleFrontend
from lingularity.frontend.console.utils.input_resolution import resolve_input, indissolubility_output
from lingularity.frontend.console.utils.output import (
    clear_screen,
    get_max_line_length_based_indentation,
    DEFAULT_VERTICAL_VIEW_OFFSET,
    erase_lines
)


class VocableAdderFrontend(VocableTrainerConsoleFrontend):
    def __init__(self, mongodb_client: MongoDBClient):
        non_english_language, train_english = self._select_training_language(mongodb_client)

        self._backend = VocableAdderBackend(non_english_language, mongodb_client)

    class Option(Enum):
        Exit = 'exit'
        AlterLatestVocableEntry = 'alter'

    def _display_training_screen_header(self):
        clear_screen()
        print(DEFAULT_VERTICAL_VIEW_OFFSET * 2)

        instructions = (
            f"Press CTRL + C in order to select one of the following options:",
            "\t  - 'exit' and return to trainer selection creates_new_view",
            "\t  - 'alter' the latest vocable entry"
        )

        indentation = get_max_line_length_based_indentation(instructions)
        for instruction in instructions:
            print(f'{indentation}{instruction}')

        print(DEFAULT_VERTICAL_VIEW_OFFSET)

    def _get_option_selection(self) -> Optional[Option]:
        erase_lines(0)
        if (option_keyword := resolve_input(input('Enter option keyword: '), options=[op.value for op in self.Option])) is not None:
            return self.Option(option_keyword)
        return None

    def _output_vocable_addition_confirmation(self):
        print(f'Added {self._latest_created_vocable_entry.line_repr}')

    def __call__(self) -> bool:
        self._display_training_screen_header()

        while True:
            try:
                n_printed_lines = self._add_vocable()
                erase_lines(n_printed_lines)
                self._output_vocable_addition_confirmation()

            except KeyboardInterrupt:
                if (option := self._get_option_selection()) is None:
                    indissolubility_output("Couldn't resolve option", sleep_duration=0.8, n_deletion_lines=2)
                    cursor.show()

                # option execution
                elif option is self.Option.Exit:
                    break

                elif self._latest_created_vocable_entry is not None:
                    n_printed_lines = self._alter_vocable_entry(self._latest_created_vocable_entry)
                    erase_lines(n_printed_lines + 1)
                    self._output_vocable_addition_confirmation()

        return True
