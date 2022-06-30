from typing import Any, List, Dict, Callable
import dataclasses

from termcolor import colored


@dataclasses.dataclass
class Option:
    description: str
    callback: Any
    keyword_index: int = 0


OFFSET = ' ' * 7


class Options:
    def __init__(self, options: List[Option], color='red', inter_option_indentation=OFFSET):
        self._keyword_2_callback: Dict[str, Any] = {option.description.split(' ')[option.keyword_index].lower(): option.callback for option in options}
        self.keywords = list(self._keyword_2_callback.keys())
        self.display_row: str = inter_option_indentation.join(self._process_descriptions(options, color=color))

    @staticmethod
    def _process_descriptions(options: List[Option], color: str) -> List[str]:
        return [color_description(option.description, keyword_index=option.keyword_index, color=color) for option in options]

    def __getitem__(self, item: str) -> Any:
        return self._keyword_2_callback[item]


def color_description(description: str, keyword_index: int, color='red') -> str:
    description_splits = description.split(' ')
    for i, split in enumerate(description_splits):
        coloring_function: Callable[[str, str], str] = _color_keyword if i == keyword_index else colored  # type: ignore
        description_splits[i] = coloring_function(split, color)

    return' '.join(description_splits)


def _color_keyword(keyword: str, color='red') -> str:
    return '(' + colored(keyword[0], color) + ')' + colored(keyword[1:], color)
