import locale
from typing import List

from backend.src.components.tts import GoogleTTSClient
from backend.src.database import UserMongoDBClient
from backend.src.metadata import language_metadata
from backend.src.ops import spacy_models, stemming
from backend.src.string_resources import string_resources
from termcolor import colored

from frontend.src.reentrypoint import ReentryPoint
from frontend.src.state import State
from frontend.src.utils import output, view
from frontend.src.utils.output.percentual_indenting import IndentedPrint
from frontend.src.utils.prompt.cancelling import QUERY_CANCELLED
from frontend.src.utils.prompt.repetition import prompt_relentlessly
from frontend.src.utils.view import Banner, terminal


# enable hundred delimiting by local convention
locale.setlocale(locale.LC_ALL, str())


@view.creator(banner=Banner('languages/3d-ascii', 'cyan'))
@State.receiver
def __call__(state: State) -> ReentryPoint:
    """ Displays languages not yet used by user, colorized in regard to their
        tts/tokenization availability in block indented manner, writes selected
        language into global state """

    eligible_languages = list(set(language_metadata.keys()) - state.user_languages)

    _render_screen(eligible_languages, state)
    return _proceed(eligible_languages, state)


def _render_screen(eligible_languages: list[str], state: State):
    terminal.set_title(['Add a new language', "Select a language you'd like to learn"][state.is_new_user])

    # group by starting letter, highlight_color languages according to tts/tokenizing availability,
    # display in output-block-indented manner
    starting_letter_grouped_languages = output.group_by_starting_letter(eligible_languages, is_sorted=False)
    colored_joined_language_groups = [
        ' '.join(map(lambda language: f'{_color_language_wrt_available_components(language)}({language_metadata[language].get("nSentences", -69):n})'.replace('-69', '∞'), language_group)) for
        language_group in starting_letter_grouped_languages]
    _display_eligible_languages(colored_joined_language_groups)

    # display legend
    legend_section_indentation = output.column_percentual_indentation(0.02)

    output.centered(
        f'Legend:{legend_section_indentation}'
        f'{colored("low", _LOW_QUALITY_NORMALIZATION_COLOR)}/'
        f'{colored("medium", _MEDIUM_QUALITY_NORMALIZATION_COLOR)}/'
        f'{colored("high", _HIGH_QUALITY_NORMALIZATION_COLOR)} '
        f'quality word normalization{legend_section_indentation}'
        f'{colored("text-to-speech available", attrs=_TTS_ATTRS)}{legend_section_indentation}'
        f'(number of available sentences)',
        end=view.VERTICAL_OFFSET
    )


def _display_eligible_languages(grouped_eligible_languages: List[str]):
    _print = IndentedPrint(output.block_centering_indentation(grouped_eligible_languages))
    for language_group in grouped_eligible_languages:
        _print(language_group)
    output.empty_row()


_HIGH_QUALITY_NORMALIZATION_COLOR = 'red'
_MEDIUM_QUALITY_NORMALIZATION_COLOR = 'magenta'
_LOW_QUALITY_NORMALIZATION_COLOR = 'cyan'
_TTS_ATTRS = ['underline']


def _color_language_wrt_available_components(language: str) -> str:
    color, attrs = None, None

    if language in GoogleTTSClient.AVAILABLE_LANGUAGES:
        attrs = _TTS_ATTRS

    if language in spacy_models.AVAILABLE_LANGUAGES:
        color = _HIGH_QUALITY_NORMALIZATION_COLOR
    elif language.lower() in stemming.AVAILABLE_LANGUAGES:
        color = _MEDIUM_QUALITY_NORMALIZATION_COLOR
    else:
        color = _LOW_QUALITY_NORMALIZATION_COLOR

    return colored(language, color=color, attrs=attrs)


def _proceed(eligible_languages: list[str], state: State) -> ReentryPoint:
    selection = prompt_relentlessly(
        'Select language: ',
        indentation_percentage=0.35,
        options=eligible_languages,
        cancelable=True
    )
    if selection == QUERY_CANCELLED:
        return ReentryPoint.Home

    UserMongoDBClient.instance().insert_dummy_entry(selection)

    # query desired reference language if English selected
    if selection == string_resources['english']:
        return _reference_language_selection_screen()

    # write language selection into state
    state.set_language(non_english_language=selection, train_english=False)
    return ReentryPoint.TrainingSelection


@view.creator(title='Reference Language Selection', banner=Banner('languages/3d-ascii', 'yellow'))
@State.receiver
def _reference_language_selection_screen(state: State) -> ReentryPoint:
    eligible_languages = list(set(language_metadata.keys()) - {string_resources.ENGLISH})
    starting_letter_grouped_languages = output.group_by_starting_letter(eligible_languages, is_sorted=False)
    _display_eligible_languages(
        grouped_eligible_languages=[
            ' '.join(map(lambda language: f'{colored(language, _HIGH_QUALITY_NORMALIZATION_COLOR, attrs=_TTS_ATTRS)}({language_metadata[language]["nSentences"]:n})', language_group)) for
            language_group in starting_letter_grouped_languages]
    )

    # query desired language
    selection = prompt_relentlessly(
        'Select reference language: ',
        indentation_percentage=0.35,
        options=eligible_languages,
        cancelable=True
    )
    if selection == QUERY_CANCELLED:
        return ReentryPoint.LanguageAddition

    UserMongoDBClient.instance().set_reference_language(reference_language=selection)
    state.set_language(non_english_language=selection, train_english=True)
    return ReentryPoint.TrainingSelection