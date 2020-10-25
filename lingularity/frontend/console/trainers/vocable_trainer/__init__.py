from typing import Optional, Tuple, List
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
from lingularity.frontend.console.trainers.sentence_translation import SentenceTranslationTrainerConsoleFrontend
from lingularity.frontend.console.trainers.base import TrainerConsoleFrontend, TrainingOptions
from lingularity.frontend.console.utils.view import view_creator, DEFAULT_VERTICAL_VIEW_OFFSET
from lingularity.frontend.console.utils.input_resolution import resolve_input, repeat
from lingularity.frontend.console.utils import matplotlib as plt_utils
from lingularity.frontend.console.utils.console import (
    erase_lines,
    centered_print,
    centered_block_indentation,
    UndoPrint,
    centered_print_indentation,
    centered_input_query,
    colorize_chars
)


_undo_print = UndoPrint()


# TODO: set up modes
#  revisit score history system

class VocableTrainerConsoleFrontend(TrainerConsoleFrontend):
    def __init__(self):
        super().__init__(Backend)

        self._accumulated_score: float = 0.0
        self._streak: int = 0
        self._perfected_entries: List[VocableEntry] = []

        self._current_vocable_entry: Optional[VocableEntry] = None

    # -----------------
    # Driver
    # -----------------
    def __call__(self) -> bool:
        self._backend.set_item_iterator()

        if self._backend.new_vocable_entries_available:  # type: ignore
            self._display_new_vocabulary_if_desired()

        self._display_training_screen_header_section()
        self._run_training()

        self._backend.enter_session_statistics_into_database(self._n_trained_items)

        if self._n_trained_items:
            self._display_pie_chart()

        self._plot_training_chronic()

        if len(self._perfected_entries):
            self._display_perfected_entries()

        return False

    # -----------------
    # Training Options
    # -----------------
    def _get_training_options(self) -> TrainingOptions:
        VocableTrainerOption.set_frontend_instance(self)
        return TrainingOptions([AddVocable,
                                AlterLatestCreatedVocableEntry,
                                AlterCurrentVocableEntry,
                                DeleteVocableEntry,
                                Exit])

    # -----------------
    # Training Property Selection
    # -----------------
    @view_creator()
    def _select_training_language(self) -> Tuple[str, bool]:
        # TODO: enable English training

        train_english = False

        # forward user to training action allowing for vocable accumulation if
        # no vocabulary available whatsoever
        if not (eligible_languages := Backend.get_eligible_languages()):
            return self._start_sentence_translation_trainer()

        # return language if only one singular available
        elif len(eligible_languages) == 1:
            return eligible_languages[0], train_english

        # display header
        centered_print('ELIGIBLE LANGUAGES', DEFAULT_VERTICAL_VIEW_OFFSET)

        # display available languages
        indentation = centered_block_indentation(eligible_languages)
        for language in sorted(eligible_languages):
            print(indentation, language)
        print('')

        # query selection
        language_selection = resolve_input(centered_input_query('Enter desired language: ', expected_response_length=5), eligible_languages)
        if language_selection is None:
            return repeat(self._select_training_language, n_deletion_lines=-1)
        print('\n')

        return language_selection, train_english

    @staticmethod
    @view_creator()
    def _start_sentence_translation_trainer():
        # TODO: forward to sentence ground_truth trainer/vocable
        #  adder selection screen

        centered_print("""You have to accumulate vocabulary by means of the 
        SentenceTranslation™ Trainer or VocableAdder first.""")
        sleep(3)

        centered_print('Initiating SentenceTranslation TrainerBackend...')
        sleep(2)

        return SentenceTranslationTrainerConsoleFrontend().__call__()

    # -----------------
    # Pre Training
    # -----------------
    @view_creator()
    def _display_new_vocabulary_if_desired(self):
        print(DEFAULT_VERTICAL_VIEW_OFFSET * 2)
        centered_print('Would you like to see the vocable entries you recently created? (y)es/(n)o')
        centered_print(' ', end='')

        if (input_resolution := resolve_input(input(''), ['yes', 'no'])) is None:
            repeat(self._display_new_vocabulary_if_desired, n_deletion_lines=-1)

        elif input_resolution == 'yes':
            self._display_new_vocable_entries()

    @view_creator()
    def _display_new_vocable_entries(self):
        print(DEFAULT_VERTICAL_VIEW_OFFSET)

        # display entry line representations
        line_reprs = list(map(lambda entry: str(entry), self._backend.new_vocable_entries))
        indentation = centered_block_indentation(line_reprs)
        for line_repr in line_reprs:
            print(indentation, line_repr)

        # wait for key press
        centered_print(f'{DEFAULT_VERTICAL_VIEW_OFFSET}PRESS ANY KEY TO CONTINUE')
        centered_input_query()

    # ------------------
    # Training
    # ------------------
    @view_creator()
    def _display_training_screen_header_section(self):
        # TODO: find better wording for 'imperfect entries', display forename origin country,
        #  elaborate usage instructions, functionality explanation

        # display number of retrieved vocables to be trained
        centered_print(f'Found {self._backend.n_training_items} imperfect entries\n\n')
        centered_print("Hit Enter to proceed after response evaluation\n")

        # display instructions
        INSTRUCTION_HEAD = f"Enter:{' ' * 34}"
        indentation = centered_print_indentation(INSTRUCTION_HEAD)

        print(f'{indentation}{INSTRUCTION_HEAD}')
        for i, instruction_row in enumerate(self._training_options.instructions):
            print(f'{indentation}  {instruction_row}')
            if i == 2:
                print(f"\n{indentation}    NOTE: distinct translations are to be delimited by ', '\n")
        print('\n')

        # display lets go
        self._output_lets_go()

    def _run_training(self):
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
            _undo_print(translation_query_output, end='')

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
            _undo_print(translation_query_output, end='')

            ground_truth_output = f'{colored(entry.vocable, "green")}'

            # merely display correct ground_truth if no response given,
            # otherwise display response and evaluation
            if response_evaluation is ResponseEvaluation.NoResponse:
                _undo_print(ground_truth_output, end='')

            else:
                if response_evaluation is ResponseEvaluation.AlmostCorrect:
                    response_deviation_mask, ground_truth_deviation_mask = deviation_masks(response=response, ground_truth=entry.vocable)

                    response = colorize_chars(response, char_mask=response_deviation_mask, color_kwargs={'color': "red"})
                    ground_truth_output = colorize_chars(entry.vocable, char_mask=ground_truth_deviation_mask, color_kwargs={'color': 'green', 'attrs': ['underline']}, fallback_color_kwargs={'color': 'green'})

                _undo_print(f'{response} | {colored(" ".join(split_at_uppercase(response_evaluation.name)).upper(), EVALUATION_2_COLOR[response_evaluation])}', end='')

                # display correct ground_truth in case of imperfect response
                if response_evaluation is not ResponseEvaluation.Correct:
                    _undo_print(f" | Correct translation: {ground_truth_output}", end='')

            # display new score in case of change having taken place
            if response_evaluation not in [ResponseEvaluation.NoResponse, ResponseEvaluation.Wrong]:
                if entry.score < 5:
                    _undo_print(f" | New Score: {[int(entry.score), entry.score][bool(entry.score % 1)]}", end='')
                else:
                    self._perfected_entries.append(entry)
                    _undo_print(" | Entry Perfected", end='')

            _undo_print('\n')

            # get related sentence pairs, convert forenames if feasible
            related_sentence_pairs = self._backend.related_sentence_pairs(entry.vocable, n=2)
            if self._backend.forenames_convertible:
                related_sentence_pairs = list(map(self._backend.forename_converter, related_sentence_pairs))

            # display sentence pairs
            for sentence_pair in related_sentence_pairs:
                centered_print(' - '.join(reversed(sentence_pair)), line_counter=_undo_print)
            _undo_print('')

            # increment/reassign attributes
            # entry.increment_times_faced()
            self._n_trained_items += 1
            self._accumulated_score += response_evaluation.value
            self._current_vocable_entry = entry
            self._update_streak(response_evaluation)

            # display absolute entry progress if n_trained_items divisible by 10
            if not self._n_trained_items % 10 and self._n_trained_items != self._backend.n_training_items:
                centered_print(f'\n{self._n_trained_items} Entries faced, {self._backend.n_training_items - self._n_trained_items} more to go\n', line_counter=_undo_print)
            _undo_print('')

            # query option/procedure, execute option if applicable
            if len((option_selection := self._query_option_selection())):
                self._training_options[option_selection].execute()
                if type(self._training_options[option_selection]) is Exit:
                    return

            # clear screen part pertaining to current entry
            _undo_print.undo()

            entry = self._backend.get_training_item()
        # TODO: make display bar advance to 100% after completion of last vocable

    def _query_option_selection(self) -> str:
        centered_print('$', end='', line_counter=_undo_print)
        if (option_selection := resolve_input(input(), self._training_options.keywords + [''])) is None:
            _undo_print.pop()
            return repeat(self._query_option_selection, n_deletion_lines=2)
        return option_selection

    def _display_progress_bar(self):
        BAR_LENGTH = 70

        percentage = self._n_trained_items / self._backend.n_training_items

        completed_string = '=' * int(BAR_LENGTH * percentage)
        impending_string = '-' * int(BAR_LENGTH - len(completed_string))

        centered_print(f"[{completed_string}{impending_string}]", end=' ', line_counter=_undo_print)
        _undo_print(f'{int(round(percentage * 100))}%\n\n')

    def _display_streak(self):
        attrs = ['bold']

        if self._streak >= 2:
            background = None

            if self._streak >= 5:
                attrs.append('blink')

                # change background every second increment starting from 7
                if self._streak >= 7:
                    background = ['on_green', 'on_yellow', 'on_blue', 'on_cyan', 'on_white'][min((self._streak - 7) // 2, 4)]

            centered_print(f'Current streak: {colored(self._streak, "red", background, attrs=attrs)}', end='', line_counter=_undo_print)
        _undo_print('\n\n')

    def _update_streak(self, response_evaluation: ResponseEvaluation):
        if response_evaluation in [ResponseEvaluation.WrongArticle,
                                   ResponseEvaluation.MissingArticle,
                                   ResponseEvaluation.AccentError,
                                   ResponseEvaluation.AlmostCorrect,
                                   ResponseEvaluation.Correct]:
            self._streak += 1

        else:
            self._streak = 0

    @view_creator('PERFECTED ENTRIES')
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
        for i, percentage in enumerate([incorrectness_percentage, correctness_percentage]):
            if percentage == 100:
                for plot_attributes in [LABELS, EXPLODE, SIZES, COLORS]:
                    plot_attributes.pop(i)
                break

        # define pie chart
        fig, ax = plt.subplots()
        ax.pie(SIZES, labels=LABELS, shadow=True, startangle=120, autopct='%1.1f%%', explode=EXPLODE, colors=COLORS)
        ax.set_title(self._performance_verdict(correctness_percentage))
        ax.axis('equal')

        # remove decimal point from accumulated score if integer
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
