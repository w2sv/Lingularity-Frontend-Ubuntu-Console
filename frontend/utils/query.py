from typing import Iterable, Optional, Callable, Tuple, Any, Sequence
import time

from frontend.utils import output


_INDISSOLUBILITY_MESSAGE = "COULDN'T RESOLVE INPUT"


INDENTATION = output.column_percentual_indentation(percentage=0.1)

# ------------------
# Input Resolution
# ------------------
def _resolve_input(_input: str, options: Iterable[str]) -> Optional[str]:
    processed_input = _input.lower().strip()
    options_starting_on_input = list(filter(lambda option: option.lower().startswith(processed_input), options))

    if len(options_starting_on_input) == 1:
        return options_starting_on_input[0]
    elif processed_input in options_starting_on_input:
        return _input
    return None


@output.cursor_hider
def indicate_erroneous_input(message=_INDISSOLUBILITY_MESSAGE, n_deletion_lines=0, sleep_duration=1.0):
    """ - Display message communicating indissolubility reason,
        - freeze program for sleep duration
        - erase n_deletion_lines last output output lines or clear screen if n_deletion_lines = -1 """

    output.centered(f'\n{message}')

    time.sleep(sleep_duration)

    if n_deletion_lines == -1:
        output.clear_screen()
    else:
        output.erase_lines(n_deletion_lines + 1)


# ------------------
# Callable Repetition
# ------------------
def repeat(function: Callable,
           n_deletion_lines: int,
           message=_INDISSOLUBILITY_MESSAGE,
           sleep_duration=1.0,
           args: Tuple[Any, ...] = ()):

    """ Args:
            function: callable to be repeated
            n_deletion_lines: output output lines to be deleted, if -1 screen will be cleared
            message: message to be displayed, communicating mistake committed by user because of which
                repetition had to be triggered
            sleep_duration: program sleep duration in ms
            args: function args which it will be provided with when being repeated
        Returns:
            result of function provided with args """

    indicate_erroneous_input(message, n_deletion_lines, sleep_duration)

    return function(*args)


def relentlessly(prompt: str,
                 options: Optional[Sequence[str]] = None,
                 correctness_verifier: Optional[Callable[[str], bool]] = None,
                 indentation_percentage=0.0,
                 error_indication_message=_INDISSOLUBILITY_MESSAGE,
                 sleep_duration=1.0,
                 query_method=input) -> str:

    """ Repeats query defined by prompt until response unambiguously
        identifying singular option element has been given """

    assert any([options, correctness_verifier])
    args = tuple(locals().values())

    if indentation_percentage:
        prompt = f'{output.column_percentual_indentation(indentation_percentage)}{prompt}'

    response = query_method(prompt)
    if options and (response := _resolve_input(response, options=options)) is None or correctness_verifier and not correctness_verifier(response):
        return repeat(relentlessly, n_deletion_lines=2, message=error_indication_message, args=args)
    return response


def centered(query_message: str = '') -> str:
    return input(f'{output.centering_indentation(query_message)}{query_message}')


YES_NO_QUERY_OUTPUT = '(Yes)/(N)o'
YES_NO_OPTIONS = ['yes', 'no']
