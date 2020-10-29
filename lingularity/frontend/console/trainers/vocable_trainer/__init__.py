from typing import Optional, List, Callable, Any
from time import sleep

import matplotlib.pyplot as plt
from termcolor import colored

from lingularity.backend.components import VocableEntry
from lingularity.backend.utils.strings import split_at_uppercase, common_start
from lingularity.backend.trainers.vocable_trainer import (
    VocableTrainerBackend as Backend,
    ResponseEvaluation,
    get_response_evaluation,
    deviation_masks
)

from lingularity.frontend.console.trainers.vocable_trainer.options import *
from lingularity.frontend.console.trainers.base import TrainerFrontend, TrainingOptions
from lingularity.frontend.console.reentrypoint import ReentryPoint
from lingularity.frontend.console.state import State
from lingularity.frontend.console.utils import view, input_resolution, matplotlib as plt_utils
from lingularity.frontend.console.utils.output import (
    erase_lines,
    centered_print,
    centered_block_indentation,
    UndoPrint,
    centered_print_indentation,
    centered_input_query,
    colorize_chars,
    cursor_hider
)


# TODO: set up modes
#  revisit score history system

class VocableTrainerFrontend(TrainerFrontend):
    def __new__(cls, *args, **kwargs):
        if not State.language_vocabulary_possessing:
            return cls._exit_on_nonexistent_vocabulary()
        return super().__new__(cls)

    @staticmethod
    @cursor_hider
    @view.view_creator(banner='bloody', banner_color='red')
    def _exit_on_nonexistent_vocabulary() -> Callable[[], ReentryPoint]:
        print('\n' * 5)

        centered_print("You have to accumulate vocabulary by means of the "
                       "SentenceTranslationTrainer or VocableAdder first "
                       "in order to use this training mode.\n\n")

        sleep(3)

        centered_print('HIT ENTER IN ORDER TO RETURN TO TRAINING SELECTION')
        input()

        return lambda: ReentryPoint.TrainingSelection

    def __init__(self):
        super().__init__(backend_type=Backend)

        self._undo_print = UndoPrint()

        self._accumulated_score: float = 0.0
        self._streak: int = 0
        self._perfected_entries: List[VocableEntry] = []

        self._current_vocable_entry: Optional[VocableEntry] = None

    def __call__(self) -> ReentryPoint:
        self._set_terminal_title()

        self._backend.set_item_iterator()

        if self._backend.new_vocable_entries_available:
            self._display_new_vocabulary_if_desired()

        self._display_training_screen_header_section()
        self._run_training_loop()

        self._backend.enter_session_statistics_into_database(self._n_trained_items)

        if self._n_trained_items:
            self._display_pie_chart()

        self._plot_training_chronic()

        if len(self._perfected_entries):
            self._display_perfected_entries()

        return ReentryPoint.TrainingSelection

    def _get_training_options(self) -> TrainingOptions:
        VocableTrainerOption.set_frontend_instance(self)
        return TrainingOptions([AddVocable,
                                AlterLatestCreatedVocableEntry,
                                AlterCurrentVocableEntry,
                                DeleteVocableEntry,
                                Exit])

    @property
    def _training_designation(self) -> str:
        return 'Vocable Training'

    # -----------------
    # Pre Training
    # -----------------
    @view.view_creator()
    def _display_new_vocabulary_if_desired(self):
        print(view.DEFAULT_VERTICAL_VIEW_OFFSET * 2)
        centered_print('Would you like to see the vocable entries you recently created? (y)es/(n)o')
        centered_print(' ', end='')

        if input_resolution.query_relentlessly(query_message='', options=['yes', 'no']) == 'yes':
            self._display_new_vocable_entries()

    @view.view_creator()
    def _display_new_vocable_entries(self):
        assert self._backend.new_vocable_entries is not None

        print(view.DEFAULT_VERTICAL_VIEW_OFFSET)

        # display entry line representations
        line_reprs = list(map(lambda entry: str(entry), self._backend.new_vocable_entries))
        indentation = centered_block_indentation(line_reprs)
        for line_repr in line_reprs:
            print(indentation, line_repr)

        # wait for key press
        centered_print(f'{view.DEFAULT_VERTICAL_VIEW_OFFSET}PRESS ANY KEY TO CONTINUE')
        centered_input_query()

    # ------------------
    # Training
    # ------------------
    @view.view_creator()
    def _display_training_screen_header_section(self):
        # TODO: find better wording for 'imperfect entries', display forename origin country,
        #  elaborate usage instructions, functionality explanation

        # display number of retrieved vocables to be trained
        centered_print(f'Found {self._backend.n_training_items} imperfect entries\n\n')
        centered_print("Hit Enter to proceed after response evaluation\n")

        # display instructions
        self._training_options.display_instructions(
            insertions_with_indices=(("    NOTE: distinct translations are to be delimited by ', '", 3), )
        )

        # display lets go
        self._output_lets_go()

    def _run_training_loop(self):
        EVALUATION_2_COLOR = {
             ResponseEvaluation.Wrong: 'red',
             ResponseEvaluation.AccentError: 'yellow',
             ResponseEvaluation.AlmostCorrect: 'yellow',
             ResponseEvaluation.WrongArticle: 'cyan',
             ResponseEvaluation.MissingArticle: 'cyan',
             ResponseEvaluation.Correct: 'green'
        }

        entry: Optional[VocableEntry] = self._backend.get_training_item()

        while entry is not None:
            self._display_streak()
            self._display_progress_bar()

            # display vocable in reference language, query ground_truth
            translation_query_output = f'\t\t{entry.meaning} = '
            self._undo_print(translation_query_output, end='')

            # get vocable identification aid if synonyms with identical
            # english ground_truth amongst training vocables
            vocable_identification_aid = ''
            if synonyms := self._backend.synonyms.get(entry.the_stripped_meaning):
                vocable_identification_aid = entry.vocable[:len(common_start(synonyms)) + 1]
                print(vocable_identification_aid, end='')

            response = input()

            # concatenate vocable identification aid, get response evaluation,
            # update vocable score, enter update into database
            response, response_evaluation = get_response_evaluation(response, entry.vocable, vocable_identification_aid)
            entry.update_score(response_evaluation.value)
            self._backend.mongodb_client.update_vocable_entry(entry.vocable, entry.score)

            # erase query line, redo ground_truth query
            erase_lines(1)
            self._undo_print(translation_query_output, end='')

            ground_truth_output = f'{colored(entry.vocable, "green")}'

            # merely display correct ground_truth if no response given,
            # otherwise display response and evaluation
            if response_evaluation is ResponseEvaluation.NoResponse:
                self._undo_print(ground_truth_output, end='')

            else:
                if response_evaluation is ResponseEvaluation.AlmostCorrect:
                    response_deviation_mask, ground_truth_deviation_mask = deviation_masks(response=response, ground_truth=entry.vocable)

                    response = colorize_chars(response, char_mask=response_deviation_mask, color_kwargs={'color': "red"})
                    ground_truth_output = colorize_chars(entry.vocable, char_mask=ground_truth_deviation_mask, color_kwargs={'color': 'green', 'attrs': ['underline']}, fallback_color_kwargs={'color': 'green'})

                self._undo_print(f'{response} | {colored(" ".join(split_at_uppercase(response_evaluation.name)).upper(), EVALUATION_2_COLOR[response_evaluation])}', end='')

                # display correct ground_truth in case of imperfect response
                if response_evaluation is not ResponseEvaluation.Correct:
                    self._undo_print(f" | Correct translation: {ground_truth_output}", end='')

            # display new score in case of change having taken place
            if response_evaluation not in [ResponseEvaluation.NoResponse, ResponseEvaluation.Wrong]:
                if entry.score < 5:
                    self._undo_print(f" | New Score: {[int(entry.score), entry.score][bool(entry.score % 1)]}", end='')
                else:
                    self._perfected_entries.append(entry)
                    self._undo_print(" | Entry Perfected", end='')

            self._undo_print('\n')

            # get related sentence pairs, convert forenames if feasible
            related_sentence_pairs = self._backend.related_sentence_pairs(entry.vocable, n=2)
            if self._backend.forename_converter is not None:
                related_sentence_pairs = list(map(self._backend.forename_converter, related_sentence_pairs))

            # display sentence pairs
            for sentence_pair in related_sentence_pairs:
                centered_print(' - '.join(reversed(sentence_pair)), line_counter=self._undo_print)
            self._undo_print('')

            # increment/reassign attributes
            # entry.increment_times_faced()
            self._n_trained_items += 1
            self._accumulated_score += response_evaluation.value
            self._current_vocable_entry = entry
            self._update_streak(response_evaluation)

            # display absolute entry progress if n_trained_items divisible by 10
            if not self._n_trained_items % 10 and self._n_trained_items != self._backend.n_training_items:
                centered_print(f'\n{self._n_trained_items} Entries faced, {self._backend.n_training_items - self._n_trained_items} more to go\n', line_counter=self._undo_print)
            self._undo_print('')

            # query option/procedure, __call__ option if applicable
            option_selection = input_resolution.query_relentlessly(query_message=f'{centered_print_indentation(" ")}$', options=self._training_options.keywords)
            self._undo_print.add_lines_to_buffer(1)
            if len(option_selection):
                self._training_options[option_selection].__call__()
                if type(self._training_options[option_selection]) is Exit:
                    return

            # clear screen part pertaining to current entry
            self._undo_print.undo()

            entry = self._backend.get_training_item()
        # TODO: make display bar advance to 100% after completion of last vocable

    def _display_progress_bar(self):
        BAR_LENGTH = 70

        percentage = self._n_trained_items / self._backend.n_training_items

        completed_string = '=' * int(BAR_LENGTH * percentage)
        impending_string = '-' * int(BAR_LENGTH - len(completed_string))

        centered_print(f"[{completed_string}{impending_string}]", end=' ', line_counter=self._undo_print)
        self._undo_print(f'{int(round(percentage * 100))}%\n\n')

    def _display_streak(self):
        attrs = ['bold']

        if self._streak >= 2:
            background = None

            if self._streak >= 5:
                attrs.append('blink')

                # change background every second increment starting from 7
                if self._streak >= 7:
                    background = ['on_green', 'on_yellow', 'on_blue', 'on_cyan', 'on_white'][min((self._streak - 7) // 2, 4)]

            centered_print(f'Current streak: {colored(str(self._streak), "red", background, attrs=attrs)}', end='', line_counter=self._undo_print)
        self._undo_print('\n\n')

    def _update_streak(self, response_evaluation: ResponseEvaluation):
        if response_evaluation in [ResponseEvaluation.WrongArticle,
                                   ResponseEvaluation.MissingArticle,
                                   ResponseEvaluation.AccentError,
                                   ResponseEvaluation.AlmostCorrect,
                                   ResponseEvaluation.Correct]:
            self._streak += 1

        else:
            self._streak = 0

    @view.view_creator('PERFECTED ENTRIES')
    def _display_perfected_entries(self):
        # TODO: revisit

        for entry in self._perfected_entries:
            centered_print(str(entry))
        print('\n\n')

    # -----------------
    # Post Training
    # -----------------
    @staticmethod
    def _performance_verdict(correctness_percentage: float) -> str:
        return {
            0: 'You suck.',
            20: 'Get your shit together m8.',
            40: "You can't climb the ladder of success with your hands in your pockets.",
            60: "Keep hustlin' young blood.",
            80: 'Attayboy!',
            100: '0361/2680494. Call me.'
        }[int(correctness_percentage) // 20 * 20]

    def _display_pie_chart(self):
        correctness_percentage = self._accumulated_score / self._n_trained_items * 100
        incorrectness_percentage = 100 - correctness_percentage

        LABELS = ['Correct', 'Incorrect']
        EXPLODE = [0.1, 0]
        SIZES = [correctness_percentage, incorrectness_percentage]
        COLORS = ['g', 'r']

        # discard plot attributes of opposing slice if either correctness percentage
        # or incorrectness percentage = 100
        PLOT_ATTRS: List[List[Any]] = [LABELS, EXPLODE, SIZES, COLORS]
        for i, percentage in enumerate([incorrectness_percentage, correctness_percentage]):
            if percentage == 100:
                for plot_attributes in PLOT_ATTRS:
                    del plot_attributes[i]
                break

        # define pie chart
        fig, ax = plt.subplots()
        ax.pie(SIZES, labels=LABELS, shadow=True, startangle=120, autopct='%1.1f%%', explode=EXPLODE, colors=COLORS)
        ax.set_title(self._performance_verdict(correctness_percentage))
        ax.axis('equal')

        # remove decimal reentry_point from accumulated score if integer
        accumulated_score = [int(self._accumulated_score), self._accumulated_score][bool(self._accumulated_score % 1)]

        fig.canvas.set_window_title(f'You got {accumulated_score}/{self._n_trained_items} right')
        plt_utils.center_window()
        plt_utils.close_window_on_button_press()

    @property
    def _item_name(self) -> str:
        return 'vocable entry'

    @property
    def _pluralized_item_name(self) -> str:
        return 'vocable entries'
