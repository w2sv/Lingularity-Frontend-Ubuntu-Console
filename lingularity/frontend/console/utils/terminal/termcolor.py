from typing import Iterator, Optional, List, Dict, Union

from termcolor import colored


ColorKwargs = Dict[str, Union[str, List[str]]]


def colorize_chars(string: str,
                   char_mask: Iterator[bool],
                   color_kwargs: ColorKwargs,
                   fallback_color_kwargs: Optional[ColorKwargs] = None) -> str:

    chars = list(string)
    for i, (apply, char) in enumerate(zip(char_mask, chars)):
        if apply:
            chars[i] = colored(char, **color_kwargs)  # type: ignore
        elif fallback_color_kwargs:
            chars[i] = colored(char, **fallback_color_kwargs)  # type: ignore
    return ''.join(chars)
