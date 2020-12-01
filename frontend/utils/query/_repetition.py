from typing import Optional, Sequence, Callable, Iterable, Tuple, Any

from frontend.utils import output
from frontend.utils.query._cancelling import CANCELLED, _cancelable, _escape_unicode_stripped
from frontend.utils.query._ops import indicate_erroneous_input, _INDISSOLUBILITY_MESSAGE


def relentlessly(prompt: str = '',
                 indentation_percentage=0.0,
                 prompt_display_function: Optional[Callable] = None,
                 options: Optional[Sequence[str]] = None,
                 applicability_verifier: Optional[Callable[[str], bool]] = None,
                 error_indication_message=_INDISSOLUBILITY_MESSAGE,
                 sleep_duration=1.0,
                 cancelable=False,
                 n_deletion_rows=2) -> str:

    """ Args:
            prompt: to be repeatedly displayed on query
            prompt_display_function: will be repeatedly invoked alongside display of prompt if passed
            options: eligible options, one of which ought to be selected
            applicability_verifier: function verifying applicability of entered response
                Note: either one of options/applicability_verifier has to be passed
            indentation_percentage: of display prompt
            error_indication_message: to be displayed on unsuccessful response validation
            sleep_duration: after display of error_indication_message
            cancelable: whether or not to enable canceling the query by means of an ESC stroke
            n_deletion_rows: n previous rows to be deleted before query repetition

        Repeats query until response either unambiguously identifiable
        amongst passed options, or causing correctness verifier
        to return True

        Returns:
            either unambiguously identified element of options or response
            having been validated by applicability_verifier """

    assert bool(options) ^ bool(applicability_verifier)

    # save args in case of repetition necessity occurring
    args = tuple(locals().values())

    # invoke prompt_display_function if passed
    if prompt_display_function:
        prompt_display_function()

    # add indentation if applicable
    if indentation_percentage:
        prompt = f'{output.column_percentual_indentation(indentation_percentage)}{prompt}'

    # query in a cancelable manner if applicable, otherwise normally
    if cancelable:
        if (response := _cancelable(prompt)) == CANCELLED:
            return CANCELLED
    else:
        response = _escape_unicode_stripped(input(prompt))

    # return given response if either unambiguously identifiable element of options or
    # applicability verified, otherwise trigger repetition
    if options and (resolved_response := _resolve_input(response, options=options)) is not None:
        return resolved_response
    elif applicability_verifier and applicability_verifier(response):
        return response
    return _repeat(relentlessly, n_deletion_rows=n_deletion_rows, message=error_indication_message, args=args)


def _resolve_input(_input: str, options: Iterable[str]) -> Optional[str]:
    """ Attempts to resolve targeted options element by means of _input

        cases of both _input and options will be leveled, however identified
        options element returned in original case

        Returns:
            element of options if unambiguously identifiable, otherwise None

        >>> _resolve_input('it', options=['Italian', 'French'])
        'Italian'
        >>> _resolve_input('It', options=['Italian', 'French'])
        'Italian'
        >>> _resolve_input('It', options=['italian', 'french'])
        'italian'
        >>> _resolve_input('i', options=['Italian', 'Icelandic'])
        """

    processed_input = _input.lower().strip()
    options_starting_on_input = list(filter(lambda option: option.lower().startswith(processed_input), options))

    if len(options_starting_on_input) == 1:
        return options_starting_on_input[0]
    elif processed_input in options_starting_on_input:
        return _input
    return None


def _repeat(function: Callable,
            n_deletion_rows: int,
            message=_INDISSOLUBILITY_MESSAGE,
            sleep_duration=1.0,
            args: Tuple[Any, ...] = ()):

    """ Args:
            function: to be repeated
            n_deletion_rows: n lines to be deleted, if -1 screen will be cleared
            message: to be displayed, communicating mistake committed by user because of which
                repetition had to be triggered
            sleep_duration: in ms
            args: which function will be provided with when being repeated
        Returns:
            result of function provided with args """

    indicate_erroneous_input(message, n_deletion_rows, sleep_duration)

    return function(*args)
