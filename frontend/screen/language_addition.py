from termcolor import colored

from backend import string_resources, language_metadata
from backend.ops.normalizing import stemming, lemmatizing
from backend.ops.google import text_to_speech

from frontend.state import State
from frontend.reentrypoint import ReentryPoint
from frontend.utils import view, query, output
from frontend.screen.ops import reference_language


@view.creator(banner='languages/3d-ascii', banner_color='cyan')
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
    colored_joined_language_groups = ['  '.join(map(_color_language_wrt_available_components, language_group)) for language_group in starting_letter_grouped_languages]
    indentation = output.block_centering_indentation(colored_joined_language_groups)
    for language_group in colored_joined_language_groups:
        print(indentation, language_group)
    print(view.VERTICAL_OFFSET)

    # TODO: display legend, add sentence volumes

    # query desired language
    selection = query.relentlessly('Select language: ', options=eligible_languages, indentation_percentage=0.35, cancelable=True)
    if selection == query.CANCELLED:
        return ReentryPoint.Home

    # query desired reference language if English selected
    train_english = False
    if selection == string_resources.ENGLISH:
        train_english = True
        selection = reference_language.procure(eligible_languages=eligible_languages)

    # write language selection into state
    State.set_language(non_english_language=selection, train_english=train_english)
    return ReentryPoint.TrainingSelection


def _color_language_wrt_available_components(language: str) -> str:
    color, attrs = None, None

    if language in text_to_speech.AVAILABLE_LANGUAGES:
        attrs = ['bold']

    if language in lemmatizing.AVAILABLE_LANGUAGES:
        color = 'red'
    elif language.lower() in stemming.AVAILABLE_LANGUAGES:
        color = 'magenta'
    else:
        color = 'cyan'

    return colored(language, color=color, attrs=attrs)
