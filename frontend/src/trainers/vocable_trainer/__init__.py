from __future__ import annotations

import time
from typing import Optional

from backend.src.trainers.vocable_trainer import (
    VocableTrainerBackend
)
from backend.src.trainers.vocable_trainer.deviation_masks import deviation_masks
from backend.src.trainers.vocable_trainer.response_evaluation import (
    EVALUATION_2_SCORE,
    get_response_evaluation,
    ResponseEvaluation
)
from backend.src.types.vocable_entry import VocableEntry
from backend.src.utils.strings.extraction import longest_common_prefix
from backend.src.utils.strings.splitting import split_at_uppercase
from termcolor import colored

from frontend.src.reentrypoint import ReentryPointProvider
from frontend.src.state import State
from frontend.src.trainers.base import SequencePlotData, TrainerFrontend
from frontend.src.trainers.base.options import base_options, TrainingOptions
from frontend.src.trainers.vocable_trainer import options
from frontend.src.utils import output as op, query, view
from frontend.src.utils.query.repetition import query_relentlessly


class VocableTrainerFrontend(TrainerFrontend[VocableTrainerBackend]):
    def __new__(cls, *args, **kwargs) -> ReentryPointProvider | VocableTrainerFrontend:
        """ Check whether vocabulary available for language, invoke vocabulary
            existence necessity information screen if not and exit afterwards """

        if not State.instance().vocabulary_available:
            return cls._exit_on_nonexistent_vocabulary()
        return super().__new__(cls)

    @staticmethod
    @op.cursor_hider
    @view.creator(banner_args=('lingularity/bloody', 'red'))
    def _exit_on_nonexistent_vocabulary():
        print(op.column_percentual_indentation(0.1))

        op.centered("You have to accumulate vocabulary by means of the "
                    "SentenceTranslationTrainer or VocableAdder first "
                    "in order to use this training mode.", view.VERTICAL_OFFSET)

        time.sleep(3)

        op.centered('HIT ENTER IN ORDER TO RETURN TO TRAINING SELECTION')
        input()

        return lambda: None

    def __init__(self):
        super().__init__(
            backend_type=VocableTrainerBackend,
            item_name='vocable entry',
            item_name_plural='vocable entries',
            training_designation='Vocable Training'
        )

        self._undo_print = op.UndoPrint()

        self._accumulated_score: float = 0.0
        self._streak: int = 0
        self._n_perfected_entries: int = 0

        self._current_vocable_entry: Optional[VocableEntry] = None

    def __call__(self) -> SequencePlotData:
        self._set_terminal_title()

        self._backend.set_item_iterator()

        if self._backend.new_vocable_entries_available:
            self._display_new_vocabulary_if_desired()

        self._display_training_screen_header_section()
        self._run_training_loop()

        self._backend.enter_session_statistics_into_database(self._n_trained_items)

        return self._training_item_sequence_plot_data()

    def _get_training_options(self) -> TrainingOptions:
        return TrainingOptions([base_options.AddVocable,
                                base_options.RectifyLatestAddedVocableEntry,
                                options.AlterCurrentVocableEntry,
                                options.DeleteVocableEntry,
                                base_options.Exit], frontend_instance=self)

    # -----------------
    # Pre Training
    # -----------------
    @view.creator(vertical_offsets=0)
    def _display_new_vocabulary_if_desired(self):
        print(op.column_percentual_indentation(0.45))
        op.centered(f'Would you like to see the vocable entries you recently created? {query.YES_NO_QUERY_OUTPUT}')
        op.centered(' ', end='')

        if query_relentlessly(prompt='', options=query.YES_NO_OPTIONS) == query.YES:
            self._display_new_vocable_entries()

    @view.creator(vertical_offsets=2)
    def _display_new_vocable_entries(self):
        assert self._backend.new_vocable_entries is not None

        # display entry line representations
        line_reprs = list(map(lambda entry: str(entry), self._backend.new_vocable_entries))
        indentation = op.block_centering_indentation(line_reprs)
        for line_repr in line_reprs:
            print(indentation, line_repr)

        # wait for key press
        op.centered(f'{view.VERTICAL_OFFSET}PRESS ANY KEY TO CONTINUE')
        query.centered()

    # ------------------
    # Training
    # ------------------
    @view.creator()
    def _display_training_screen_header_section(self):
        # TODO: elaborate usage instructions, functionality explanation

        # display number of retrieved vocables to be trained
        op.centered(f'Found {self._backend.n_training_items} entries to be practiced{view.VERTICAL_OFFSET}')
        op.centered("Hit Enter to proceed after response evaluation\n")

        # display instructions
        self._training_options.display_instructions(
            insertion_args=((3, "    NOTE: distinct translations are to be delimited by ', '", False),)
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
            if synonyms := self._backend.paraphrases.get(entry.the_stripped_meaning):
                vocable_identification_aid = entry.vocable[:len(longest_common_prefix(synonyms)) + 1]
                print(vocable_identification_aid, end='')

            response = input()

            # concatenate vocable identification aid, get response evaluation,
            # update vocable score, enter update into database
            response, response_evaluation = get_response_evaluation(response, entry.vocable, vocable_identification_aid)
            entry.update_score(response_evaluation.value)
            self._backend.user_mongo_client.update_vocable_entry(entry.vocable, entry.score)

            # erase query line, redo ground_truth query
            op.erase_lines(1)
            self._undo_print(translation_query_output, end='')

            ground_truth_output = f'{colored(entry.vocable, "green")}'

            # merely display correct ground_truth if no response given,
            # otherwise display response and evaluation
            if response_evaluation is ResponseEvaluation.NoResponse:
                self._undo_print(ground_truth_output, end='')

            else:
                if response_evaluation is ResponseEvaluation.AlmostCorrect:
                    response_deviation_mask, ground_truth_deviation_mask = deviation_masks(response=response, ground_truth=entry.vocable)

                    response = op.colorize_chars(response, char_mask=response_deviation_mask, color_kwargs={'color': "red"})
                    ground_truth_output = op.colorize_chars(entry.vocable, char_mask=ground_truth_deviation_mask, color_kwargs={'color': 'green', 'attrs': ['underline']}, fallback_color_kwargs={'color': 'green'})

                self._undo_print(f'{response} | {colored(" ".join(split_at_uppercase(response_evaluation.name)).upper(), EVALUATION_2_COLOR[response_evaluation])}', end='')

                # display correct ground_truth in case of imperfect response
                if response_evaluation is not ResponseEvaluation.Correct:
                    self._undo_print(f" | Correct translation: {ground_truth_output}", end='')

            # display new score in case of change having taken place
            if response_evaluation not in {ResponseEvaluation.NoResponse, ResponseEvaluation.Wrong}:
                if entry.score < 5:
                    self._undo_print(f" | New Score: {[int(entry.score), entry.score][bool(entry.score % 1)]}", end='')
                else:
                    self._n_perfected_entries += 1
                    self._undo_print(" | Entry Perfected", end='')

            self._undo_print('\n')

            # get related sentence pairs, convert forenames if feasible
            related_sentence_pairs = self._backend.related_sentence_pairs(entry.vocable, n=2)
            if self._backend.forename_converter is not None:
                related_sentence_pairs = list(map(self._backend.forename_converter, related_sentence_pairs))

            # display sentence pairs
            for sentence_pair in related_sentence_pairs:
                op.centered(' - '.join(reversed(sentence_pair)), line_counter=self._undo_print)
            self._undo_print('')

            # increment/reassign attributes
            # entry.increment_times_faced()
            self._n_trained_items += 1
            self._accumulated_score += EVALUATION_2_SCORE[response_evaluation]
            self._current_vocable_entry = entry
            self._update_streak(response_evaluation)

            # display absolute entry progress if n_trained_items divisible by 10
            if not self._n_trained_items % 10 and self._n_trained_items != self._backend.n_training_items:
                op.centered(f'\n{self._n_trained_items} Entries faced, {self._backend.n_training_items - self._n_trained_items} more to go\n', line_counter=self._undo_print)
            self._undo_print('')

            # query option/procedure, __call__ option if applicable
            option_selection = query_relentlessly(prompt=f'{op.centering_indentation(" ")}$',
                                                  options=self._training_options.keywords)
            self._undo_print.add_rows_to_buffer(1)

            if len(option_selection):
                self._training_options[option_selection].__call__()

                if self._training_options.exit_training:
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

        op.centered(f"[{completed_string}{impending_string}]", end=' ', line_counter=self._undo_print)
        self._undo_print(f'{int(round(percentage * 100))}%{view.VERTICAL_OFFSET}')

    def _display_streak(self):
        attrs = ['bold']

        if self._streak >= 2:
            background = None

            if self._streak >= 5:
                attrs.append('blink')

                # change background every second increment starting from 7
                if self._streak >= 7:
                    background = ['on_green', 'on_yellow', 'on_blue', 'on_cyan', 'on_white'][min((self._streak - 7) // 2, 4)]

            op.centered(f'Current streak: {colored(str(self._streak), "red", background, attrs=attrs)}', end='', line_counter=self._undo_print)
        self._undo_print('\n\n')

    def _update_streak(self, response_evaluation: ResponseEvaluation):
        if response_evaluation in {
            ResponseEvaluation.WrongArticle,
            ResponseEvaluation.MissingArticle,
            ResponseEvaluation.AccentError,
            ResponseEvaluation.AlmostCorrect,
            ResponseEvaluation.Correct
        }:
            self._streak += 1
        else:
            self._streak = 0
