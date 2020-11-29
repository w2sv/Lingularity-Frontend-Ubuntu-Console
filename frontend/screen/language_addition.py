from typing import List
import locale

from termcolor import colored

from backend import MongoDBClient
from backend import string_resources, language_metadata
from backend.ops.normalizing import stemming, lemmatizing
from backend.ops.google import text_to_speech

from frontend.state import State
from frontend.reentrypoint import ReentryPoint
from frontend.utils import view, query, output


locale.setlocale(locale.LC_ALL, '')


@view.creator(banner_args=('languages/3d-ascii', 'cyan'))
def __call__() -> ReentryPoint:
    """ Displays languages not yet used by user, colorized with regards to their
        tts/tokenization availability in block indented manner, writes selected
        language into global state """

    view.set_terminal_title(['Add a new language', "Select a language you'd like to learn"][State.is_new_user])

    # strip languages already used by user from eligible ones
    eligible_languages = list(set(language_metadata.keys()) - State.user_languages)

    # group by starting letter, color languages according to tts/tokenizing availability,
    # display in output-block-indented manner
    starting_letter_grouped_languages = output.group_by_starting_letter(eligible_languages, is_sorted=False)
    colored_joined_language_groups = [' '.join(map(lambda language: f'{_color_language_wrt_available_components(language)}({language_metadata[language].get("nSentences", -69):n})'.replace('-69', '∞'), language_group)) for language_group in starting_letter_grouped_languages]
    indentation = _display_eligible_languages(colored_joined_language_groups)

    # display legend
    LEGEND_ELEMENT_INDENTATION = output.column_percentual_indentation(0.02)
    print(f'{indentation} '
          f'Legend:{LEGEND_ELEMENT_INDENTATION}'
          f'{colored("low", _LOW_QUALITY_NORMALIZATION_COLOR)}/'
          f'{colored("medium", _MEDIUM_QUALITY_NORMALIZATION_COLOR)}/'
          f'{colored("high", _HIGH_QUALITY_NORMALIZATION_COLOR)} '
          f'quality word normalization{LEGEND_ELEMENT_INDENTATION}'
          f'{colored("text-to-speech available", attrs=["bold"])}{LEGEND_ELEMENT_INDENTATION}'
          f'(number of available sentences)', view.VERTICAL_OFFSET)

    # query desired language
    selection = query.relentlessly('Select language: ', options=eligible_languages, indentation_percentage=0.35, cancelable=True)
    if selection == query.CANCELLED:
        return ReentryPoint.Home

    # query desired reference language if English selected
    elif selection == string_resources.ENGLISH:
        return _reference_language_selection_screen()

    # write language selection into state
    State.set_language(non_english_language=selection, train_english=False)
    return ReentryPoint.TrainingSelection


def _display_eligible_languages(grouped_eligible_languages: List[str]) -> str:
    indentation = output.block_centering_indentation(grouped_eligible_languages)
    for language_group in grouped_eligible_languages:
        print(indentation, language_group)
    print(output.EMPTY_ROW)

    return indentation


_HIGH_QUALITY_NORMALIZATION_COLOR = 'red'
_MEDIUM_QUALITY_NORMALIZATION_COLOR = 'magenta'
_LOW_QUALITY_NORMALIZATION_COLOR = 'cyan'
_TTS_ATTRS = ['bold']


def _color_language_wrt_available_components(language: str) -> str:
    color, attrs = None, None

    if language in text_to_speech.AVAILABLE_LANGUAGES:
        attrs = _TTS_ATTRS

    if language in lemmatizing.AVAILABLE_LANGUAGES:
        color = _HIGH_QUALITY_NORMALIZATION_COLOR
    elif language.lower() in stemming.AVAILABLE_LANGUAGES:
        color = _MEDIUM_QUALITY_NORMALIZATION_COLOR
    else:
        color = _LOW_QUALITY_NORMALIZATION_COLOR

    return colored(language, color=color, attrs=attrs)


@view.creator(title='Reference Language Selection', banner_args=('languages/3d-ascii', 'yellow'))
def _reference_language_selection_screen() -> ReentryPoint:
    eligible_languages = list(set(language_metadata.keys()) - {string_resources.ENGLISH})
    starting_letter_grouped_languages = output.group_by_starting_letter(eligible_languages, is_sorted=False)
    _display_eligible_languages(grouped_eligible_languages=[' '.join(map(lambda language: f'{colored(language, _HIGH_QUALITY_NORMALIZATION_COLOR, attrs=_TTS_ATTRS)}({language_metadata[language]["nSentences"]:n})', language_group)) for language_group in starting_letter_grouped_languages])

    # query desired language
    selection = query.relentlessly('Select reference language: ', options=eligible_languages, indentation_percentage=0.35, cancelable=True)
    if selection == query.CANCELLED:
        return ReentryPoint.LanguageAddition

    MongoDBClient.get_instance().set_reference_language(reference_language=selection)
    State.set_language(non_english_language=selection, train_english=True)
    return ReentryPoint.TrainingSelection
