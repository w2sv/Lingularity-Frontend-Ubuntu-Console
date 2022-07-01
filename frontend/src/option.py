from __future__ import annotations

from typing import Callable, Iterator
import dataclasses

from termcolor import colored

from frontend.src.reentrypoint import ReentryPoint


@dataclasses.dataclass
class Option:
    keyword: str
    description: str
    callback: Callable | ReentryPoint


OFFSET = ' ' * 7


class OptionCollection(dict):
    def __init__(self, options: list[Option], highlight_color='red'):
        super().__init__({option.keyword: option.callback for option in options})

        self.formatted_descriptions = list(
            map(
                lambda option: formatted_description(option, color=highlight_color),
                options
            )
        )

    def as_row(self, inter_indentation=OFFSET) -> str:
        return inter_indentation.join(self.formatted_descriptions)


def formatted_description(option: Option, color='red') -> str:
    def formatted_splits(splits: list[str]) -> Iterator[str]:
        for split in splits:
            coloring_function = _colored_keyword if split.lower() == option.keyword else colored
            yield coloring_function(split, color)  # type: ignore

    return ' '.join(formatted_splits(splits=option.description.split(' ')))


def _colored_keyword(keyword: str, color: str) -> str:
    return '(' + colored(keyword[0], color) + ')' + colored(keyword[1:], color)
