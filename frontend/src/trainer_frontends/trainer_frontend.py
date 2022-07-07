from __future__ import annotations

from abc import ABC, abstractmethod
from time import sleep

from typing import Callable, Generic, Type, TypeVar

from backend.src.metadata import language_metadata
from backend.src.trainers.trainer_backend import TrainerBackend
from backend.src.types.vocable_entry import VocableEntry
from pynput.keyboard import Controller as KeyboardController

from frontend.src.state import State
from frontend.src.trainer_frontends.option_collection import OptionCollection
from frontend.src.sequence_plot_data import SequencePlotData
from frontend.src.utils import output, view
from frontend.src.utils.prompt.cancelling import QUERY_CANCELLED
from frontend.src.utils.prompt.repetition import prompt_relentlessly
from frontend.src.utils.view import terminal


_Backend = TypeVar('_Backend', bound=TrainerBackend)
_Frontend = TypeVar('_Frontend', bound='TrainerFrontend')


class TrainerFrontend(ABC, Generic[_Backend]):
    OptionKeyword2InstructionAndFunction = dict[str, tuple[str, Callable[[_Frontend], None]]]

    @State.receiver
    def __init__(self,
                 backend_type: Type[_Backend],
                 item_name: str,
                 item_name_plural: str,
                 training_designation: str,
                 state: State,
                 option_keyword_2_instruction_and_function: OptionKeyword2InstructionAndFunction | None = None):

        self._backend: _Backend = backend_type(state.non_english_language, state.train_english)

        self._options: OptionCollection = self._assemble_options_collection(option_keyword_2_instruction_and_function)

        self._n_trained_items: int = 0
        self._latest_created_vocable_entry: VocableEntry | None = None

        self._item_name = item_name
        self._item_name_plural = item_name_plural

        self._training_designation = training_designation

        self.exit_training = False

    def _assemble_options_collection(self, keyword_2_instruction_and_function: OptionKeyword2InstructionAndFunction | None) -> OptionCollection:
        return OptionCollection(
            {
                'quit': ('Quit and return to training selection screen', self._quit),
                'add': (f'Add a new vocable to your {State.instance().language} list', self._add_vocable)
            } | (keyword_2_instruction_and_function or {})
        )

    # -----------------
    # Driver
    # -----------------
    @abstractmethod
    def __call__(self) -> SequencePlotData | None:
        """ Invokes trainer frontend

            Returns:
                reentry point """

    def _set_terminal_title(self):
        terminal.set_title(f'{self._backend.language} {self._training_designation}')

    # -----------------
    # Pre Training
    # -----------------
    @abstractmethod
    def _display_training_screen_header_section(self):
        pass

    def _output_lets_go(self):
        output.centered(language_metadata[self._backend.language]['translations'].get('letsGo') or "Let's go!", view.VERTICAL_OFFSET)

    # -----------------
    # Training
    # -----------------
    @abstractmethod
    def _training_loop(self):
        pass

    def _inquire_option_selection(self, indentation_percentage=0.0) -> bool:
        response = prompt_relentlessly(
            '$',
            indentation_percentage=indentation_percentage,
            options=list(self._options.keys()) + [str()]
        )

        try:
            self._options[response]()
            return True
        except KeyError:
            return False

    def _add_vocable(self, cancelable=False) -> bool:
        """ Query, create new vocable entry,
            Enter it into database
            Update State.vocabulary_available

            Returns:
                cancellation_flag: bool """

        # query vocable and meaning, exit if one of the two fields empty
        entry_fields = ['', '']
        for i, query_message in enumerate([f'Enter {self._backend.language} word/phrase: ', 'Enter meaning(s): ']):
            if (
                    field := prompt_relentlessly(
                        prompt=f'{output.column_percentual_indentation(percentage=0.32)}{query_message}',
                        applicability_verifier=lambda response: bool(len(response)),
                        error_indication_message="INPUT FIELD LEFT UNFILLED",
                        cancelable=cancelable
                    )
            ) == QUERY_CANCELLED:
                return True

            entry_fields[i] = field

        # create new vocable entry, enter into database
        self._latest_created_vocable_entry = VocableEntry.new(*entry_fields)
        self._backend.user_database.vocabulary_collection.upsert_entry(self._latest_created_vocable_entry)

        output.erase_lines(3)
        return False

    def _alter_vocable_entry(self, vocable_entry: VocableEntry) -> int:
        """ Returns:
                number of printed lines: int """

        # store old properties for comparison, database identification
        old_line_repr = str(vocable_entry)
        old_vocable = vocable_entry.vocable

        # type indented old representation
        KeyboardController().type(f'{output.centering_indentation(old_line_repr)}{old_line_repr}')
        # TODO: debug print(centering_indentation) into KeyboardController().type(old_line_repr)

        # get new components, i.e. vocable + ground_truth
        new_entry_components = input('').split(' - ')

        # exit in case of invalid alteration
        if len(new_entry_components) != 2:
            output.centered('INVALID ALTERATION')
            sleep(1)
            return 3

        # strip whitespaces, alter vocable entry
        stripped_new_entry_components = map(lambda component: component.strip(' '), new_entry_components)
        vocable_entry.alter(*stripped_new_entry_components)

        # insert altered entry into database in case of alteration actually having taken place
        if str(vocable_entry) != old_line_repr:
            self._backend.user_database.vocabulary_collection.alter_entry(old_vocable, vocable_entry)

        return 2

    def _quit(self):
        self.exit_training = True

    # -----------------
    # Post Training
    # -----------------
