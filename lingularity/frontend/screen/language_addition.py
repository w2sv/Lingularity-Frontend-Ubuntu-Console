from nltk.stem import SnowballStemmer
from termcolor import colored

from lingularity.backend.utils import spacy, string_resources
from lingularity.backend.ops.google.text_to_speech import google_tts
from lingularity.backend.metadata import language_metadata

from .ops import reference_language
from lingularity.frontend.state import State
from lingularity.frontend.utils import view, query, output


@view.view_creator(title='Language Addition', banner='languages/3d-ascii', banner_color='cyan')
def __call__():
    """ Displays languages not yet used by user, colorized with regards to their
        tts/tokenization availability in block indented manner, writes selected
        language into global state """

    # strip languages already used by user from eligible ones
    eligible_languages = list(set(language_metadata.keys()) - State.user_languages)

    # group by starting letter, color languages according to tts/tokenizing availability,
    # display in output-block-indented manner
    starting_letter_grouped_languages = output.group_by_starting_letter(eligible_languages, is_sorted=False)
    colored_joined_language_groups = ['  '.join(map(_color_language_wrt_available_components, language_group)) for language_group in starting_letter_grouped_languages]
    indentation = output.centered_block_indentation(colored_joined_language_groups)
    for language_group in colored_joined_language_groups:
        print(indentation, language_group)
    print(view.VERTICAL_OFFSET)

    # TODO: display legend

    # query desired language
    selection = query.relentlessly(
        f'{query.HORIZONTAL_OFFSET}Select language: ',
        options=eligible_languages
    )

    # query desired reference language if English selected
    train_english = False
    if selection == string_resources.ENGLISH:
        train_english = True
        selection = reference_language.procure(eligible_languages=eligible_languages)

    # write language selection into state
    State.set_language(non_english_language=selection, train_english=train_english)


def _color_language_wrt_available_components(language: str) -> str:
    color, attrs = None, None

    if google_tts.available_for(language):
        attrs = ['bold']

    if language in spacy.ELIGIBLE_LANGUAGES:
        color = 'red'
    elif language.lower() in SnowballStemmer.languages:
        color = 'magenta'
    else:
        color = 'cyan'

    return colored(language, color=color, attrs=attrs)
