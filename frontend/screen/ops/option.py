from typing import Any, List, Dict, Callable
import dataclasses

from termcolor import colored


OFFSET = ' ' * 7


def color_description(description: str, keyword_index: int, color='red') -> str:
    description_splits = description.split(' ')
    for i, split in enumerate(description_splits):
        coloring_function: Callable[[str, str], str] = color_keyword if i == keyword_index else colored  # type: ignore
        description_splits[i] = coloring_function(split, color)

    return' '.join(description_splits)


def color_keyword(keyword: str, color='red') -> str:
    return '(' + colored(keyword[0], color) + ')' + colored(keyword[1:], color)


@dataclasses.dataclass
class Option:
    description: str
    callback: Any
    keyword_index: int = 0


class Options:
    def __init__(self, options: List[Option], color: str):
        self._keyword_2_callback: Dict[str, Any] = {option.description.split(' ')[option.keyword_index].lower(): option.callback for option in options}
        self.keywords = list(self._keyword_2_callback.keys())
        self.display_row: str = OFFSET.join(self._process_descriptions(options, color=color))

    @staticmethod
    def _process_descriptions(options: List[Option], color: str) -> List[str]:
        return [color_description(option.description, keyword_index=option.keyword_index, color=color) for option in options]

    def __getitem__(self, item: str) -> Any:
        return self._keyword_2_callback[item]


if __name__ == '__main__':
    _options = Options(
        options=[
            Option('Translate Sentences', keyword_index=1, callback=None),
            Option('Train Vocabulary', keyword_index=1, callback=None),
            Option('Add Vocabulary', keyword_index=0, callback=None),
            Option('Quit', callback=None)],
        color='red'
    )

