from enum import Enum

from lingularity.backend.trainers import VocableAdderBackend

from lingularity.frontend.console.state import State
from lingularity.frontend.console.reentrypoint import ReentryPoint
from lingularity.frontend.console.trainers import VocableTrainerConsoleFrontend
from lingularity.frontend.console.utils import input_resolution, output, view


class VocableAdderFrontend(VocableTrainerConsoleFrontend):
    def __init__(self):
        self._backend = VocableAdderBackend(State.language)

    def __call__(self) -> ReentryPoint:
        view.set_terminal_title(f'{self._backend.language} Vocable Adding')

        self._display_training_screen_header_section()
        self._run_training_loop()

        return ReentryPoint.TrainingSelection

    class Option(Enum):
        Exit = 'exit'
        AlterLatestVocableEntry = 'alter'

    @view.view_creator()
    def _display_training_screen_header_section(self):
        instructions = (
            f"Press CTRL + C in order to select one of the following options:",
            "\t  - 'exit' and return to trainer selection view_creator",
            "\t  - 'alter' the latest vocable entry"
        )

        indentation = output.centered_block_indentation(instructions)
        for instruction in instructions:
            print(f'{indentation}{instruction}')

        print(view.DEFAULT_VERTICAL_VIEW_OFFSET)

    def _run_training_loop(self):
        response_options = [option.value for option in self.Option] + ['']

        while True:
            n_printed_lines = self._add_vocable()
            output.erase_lines(n_printed_lines)
            self._output_vocable_addition_confirmation()

            response = input_resolution.query_relentlessly(f'{output.centered_print_indentation(" ")}$', options=response_options)
            if len(response):
                option = self.Option(response)

                if option is self.Option.AlterLatestVocableEntry and self._latest_created_vocable_entry:
                    n_printed_lines = self._alter_vocable_entry(self._latest_created_vocable_entry)
                    output.erase_lines(n_printed_lines + 1)
                    self._output_vocable_addition_confirmation()

                else:
                    break

    def _output_vocable_addition_confirmation(self):
        print(f'Added {str(self._latest_created_vocable_entry)}')
