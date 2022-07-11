from backend.src.utils.strings.extraction import longest_common_prefix
from backend.src.utils.strings.transformation import strip_multiple

from frontend.src.utils import view
from frontend.src.utils.output import block_centering_indentation, empty_row
from frontend.src.utils.prompt.repetition import prompt_relentlessly
from frontend.src.utils.view import Banner


@view.creator(
        title='TTS Accent Selection',
        banner=Banner('accents/larry-3d', 'blue'),
        vertical_offsets=2
    )
def __call__(tts_accent_choices: list[str]) -> str:
    """ Returns:
            selected language variety: element of language_variety_choices """

    # discard overlapping variety parts
    common_start_length = len(longest_common_prefix(tts_accent_choices))
    processed_varieties = [strip_multiple(dialect[common_start_length:], strings=list('()')) for dialect in tts_accent_choices]

    # display eligible varieties
    indentation = block_centering_indentation(processed_varieties)
    for variety in processed_varieties:
        print(indentation, variety)
    empty_row(times=2)

    # query variety
    dialect_selection = prompt_relentlessly(
        prompt='Enter desired variety: ',
        indentation_percentage=0.37,
        options=processed_varieties
    )
    return tts_accent_choices[processed_varieties.index(dialect_selection)]