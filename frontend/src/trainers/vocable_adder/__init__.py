from backend.src.trainers import VocableAdderBackend
from termcolor import colored

from frontend.src.trainers.trainer_frontend import TrainerFrontend
from frontend.src.utils import output, view
from frontend.src.utils.view import Banner


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
        self._training_loop()

    @view.creator(banner=Banner('vocable-adder/ansi-shadow', 'blue'))
    def _display_training_screen_header_section(self):
        self._options.display_instructions()
        output.empty_row()

    def _training_loop(self):
        output.empty_row()

        if self._add_vocable(cancelable=True):
            return

        self._output_vocable_addition_confirmation()

        if self._inquire_option_selection(indentation_percentage=0.49) and self.exit_training:
            return

        output.erase_lines(2)
        return self._training_loop()

    def _output_vocable_addition_confirmation(self):
        output.centered(f'{colored("Added", color="cyan")} {str(self._latest_created_vocable_entry)}')
