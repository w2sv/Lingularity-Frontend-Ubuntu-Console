from termcolor import colored

from frontend.src.trainer_frontends.sentence_translation import MODE_2_EXPLANATION, SentenceFilterMode
from frontend.src.utils import view
from frontend.src.utils.output import block_centering_indentation
from frontend.src.utils.output.percentual_indenting import IndentedPrint
from frontend.src.utils.prompt import PROMPT_INDENTATION
from frontend.src.utils.prompt.repetition import prompt_relentlessly
from frontend.src.utils.view import Banner


@view.creator(banner=Banner('mode/3d-ascii', color='cyan'))
def __call__() -> SentenceFilterMode:

    # display eligible modes
    _print = IndentedPrint(indentation=block_centering_indentation(MODE_2_EXPLANATION.values()))
    for mode, explanation in MODE_2_EXPLANATION.items():
        _print(colored(f'{mode.display_name}:', color='red'))
        _print(f'\t{explanation}\n')

    print(view.VERTICAL_OFFSET)

    return SentenceFilterMode[
        prompt_relentlessly(
            f'{PROMPT_INDENTATION}Enter desired mode: ',
            options=[mode.name for mode in MODE_2_EXPLANATION]
        )
    ]