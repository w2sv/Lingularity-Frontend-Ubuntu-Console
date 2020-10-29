from termcolor import colored

from lingularity.backend.trainers import VocableAdderBackend as Backend

from .options import *
from lingularity.frontend.console.reentrypoint import ReentryPoint
from lingularity.frontend.console.trainers.base import TrainerFrontend, TrainingOptions
from lingularity.frontend.console.utils import input_resolution, output, view


class VocableAdderFrontend(TrainerFrontend):
    def __init__(self):
        super().__init__(backend_type=Backend)

    def __call__(self) -> ReentryPoint:
        self._set_terminal_title()

        self._display_training_screen_header_section()
        self._run_training_loop()

        return ReentryPoint.TrainingSelection

    @property
    def _training_designation(self) -> str:
        return 'Vocable Adding'

    def _get_training_options(self) -> TrainingOptions:
        return TrainingOptions(option_classes=[AlterLatestCreatedVocableEntry, Exit])

    @property
    def _item_name(self) -> str:
        return ''

    @property
    def _pluralized_item_name(self) -> str:
        return ''

    @view.view_creator(banner='vocable-adder', banner_color='blue')
    def _display_training_screen_header_section(self):
        self._training_options.display_instructions()
        print('\n')

    def _run_training_loop(self):
        while True:
            output.empty_row()

            n_printed_lines = self._add_vocable()
            output.erase_lines(n_printed_lines)

            self._output_vocable_addition_confirmation()

            response = input_resolution.query_relentlessly(f'{output.centered_print_indentation("Enter option/Proceed via Enter Stroke")}$', options=self._training_options.keywords)
            if len(response):
                self._training_options[response].__call__()
                if type(self._training_options[response] is Exit):
                    return

            output.erase_lines(2)

    def _output_vocable_addition_confirmation(self):
        output.centered_print(f'{colored("Added", color="cyan")} {str(self._latest_created_vocable_entry)}')
