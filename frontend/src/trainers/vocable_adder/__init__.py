from termcolor import colored

from backend.src.trainers import VocableAdderBackend

from frontend.src.trainers.base import TrainerFrontend
from frontend.src.trainers.base.options import TrainingOptions
from frontend.src.trainers.base.options import base_options
from frontend.src.utils import query, output as op
from frontend.src.utils import view


class VocableAdderFrontend(TrainerFrontend):
    def __init__(self):
        super().__init__(
            backend_type=VocableAdderBackend,
            item_name=str(),
            item_name_plural=str(),
            training_designation='Vocable Adding'
        )
        self._backend: VocableAdderBackend

    def __call__(self):
        self._set_terminal_title()

        self._display_training_screen_header_section()
        self._run_training_loop()

    def _get_training_options(self) -> TrainingOptions:
        return TrainingOptions(
            option_classes=[base_options.RectifyLatestAddedVocableEntry, base_options.Exit],
            frontend_instance=self
        )

    @view.creator(banner_args=('vocable-adder/ansi-shadow', 'blue'))
    def _display_training_screen_header_section(self):
        self._training_options.display_instructions()
        op.empty_row()

    def _run_training_loop(self):
        add_vocable = base_options.AddVocable(cancelable=True)

        while True:
            op.empty_row()

            if add_vocable():
                return

            self._output_vocable_addition_confirmation()

            response = query.relentlessly('$', indentation_percentage=0.49, options=self._training_options.keywords)
            if len(response):
                self._training_options[response].__call__()

                if self._training_options.exit_training:
                    return

            op.erase_lines(2)

    def _output_vocable_addition_confirmation(self):
        op.centered(f'{colored("Added", color="cyan")} {str(self._latest_created_vocable_entry)}')
