from typing import Optional
from enum import Enum

import cursor

from lingularity.backend.trainers import VocableAdderBackend
from lingularity.backend.database import MongoDBClient
from lingularity.frontend.console.trainers import VocableTrainerConsoleFrontend
from lingularity.frontend.console.utils.input_resolution import resolve_input, indicate_indissolubility
from lingularity.frontend.console.utils.terminal import (
    clear_screen,
    centered_output_block_indentation,
    erase_lines
)
from lingularity.frontend.console.utils.view import DEFAULT_VERTICAL_VIEW_OFFSET


class VocableAdderFrontend(VocableTrainerConsoleFrontend):
    def __init__(self, mongodb_client: MongoDBClient):
        non_english_language, train_english = self._select_training_language(mongodb_client)

        self._backend = VocableAdderBackend(non_english_language, mongodb_client)

    class Option(Enum):
        Exit = 'exit'
        AlterLatestVocableEntry = 'alter'

    def _display_training_screen_header_section(self):
        clear_screen()
        print(DEFAULT_VERTICAL_VIEW_OFFSET * 2)

        instructions = (
            f"Press CTRL + C in order to select one of the following options:",
            "\t  - 'exit' and return to trainer selection view_creator",
            "\t  - 'alter' the latest vocable entry"
        )

        indentation = centered_output_block_indentation(instructions)
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
        self._display_training_screen_header_section()

        while True:
            try:
                n_printed_lines = self._add_vocable()
                erase_lines(n_printed_lines)
                self._output_vocable_addition_confirmation()

            except KeyboardInterrupt:
                if (option := self._get_option_selection()) is None:
                    indicate_indissolubility(n_deletion_lines=2, message="Couldn't resolve option")
                    cursor.show()

                # option execution
                elif option is self.Option.Exit:
                    break

                elif self._latest_created_vocable_entry is not None:
                    n_printed_lines = self._alter_vocable_entry(self._latest_created_vocable_entry)
                    erase_lines(n_printed_lines + 1)
                    self._output_vocable_addition_confirmation()

        return True
