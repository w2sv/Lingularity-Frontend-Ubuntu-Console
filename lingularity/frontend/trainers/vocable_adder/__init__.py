from termcolor import colored

from lingularity.backend.trainers import VocableAdderBackend as Backend

from lingularity.frontend.reentrypoint import ReentryPoint
from lingularity.frontend.trainers.base import TrainerFrontend
from lingularity.frontend.trainers.base.options import TrainingOptions, base_options
from lingularity.frontend.utils import input_resolution, output, view


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
        return TrainingOptions(option_classes=[base_options.RectifyLatestAddedVocableEntry, base_options.Exit], frontend_instance=self)

    @property
    def _item_name(self) -> str:
        return ''

    @property
    def _pluralized_item_name(self) -> str:
        return ''

    @view.view_creator(banner='vocable-adder/ansi-shadow', banner_color='blue')
    def _display_training_screen_header_section(self):
        self._training_options.display_instructions()
        print('\n')

    def _run_training_loop(self):
        add_vocable = base_options.AddVocable()

        while True:
            output.empty_row()

            add_vocable()

            self._output_vocable_addition_confirmation()

            response = input_resolution.query_relentlessly(f'{output.centered_print_indentation("Enter option/Proceed via Enter Stroke")}$', options=self._training_options.keywords)
            if len(response):
                self._training_options[response].__call__()

                if self._training_options.exit_training:
                    return

            output.erase_lines(2)

    def _output_vocable_addition_confirmation(self):
        output.centered_print(f'{colored("Added", color="cyan")} {str(self._latest_created_vocable_entry)}')
