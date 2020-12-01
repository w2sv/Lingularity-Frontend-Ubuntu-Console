from typing import Iterator, Optional, List, Dict, Union

from termcolor import colored


_ColorKwargs = Dict[str, Union[str, List[str]]]


def colorize_chars(string: str,
                   char_mask: Iterator[bool],
                   color_kwargs: _ColorKwargs,
                   fallback_color_kwargs: Optional[_ColorKwargs] = None) -> str:
    """ Args:
            string: whose chars ought to be colorized
            char_mask: to be of length parity with string; denoting chars
                for which color_kwargs ought to be applied if corresponding
                element set to True, fallback_kwargs otherwise if passed
            color_kwargs: {termcolor.colored keyword: value}
            fallback_color_kwargs: see above """

    chars = list(string)
    for i, (apply, char) in enumerate(zip(char_mask, chars)):
        if apply:
            chars[i] = colored(char, **color_kwargs)  # type: ignore
        elif fallback_color_kwargs:
            chars[i] = colored(char, **fallback_color_kwargs)  # type: ignore
    return ''.join(chars)
