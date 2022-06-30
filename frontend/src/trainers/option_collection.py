from __future__ import annotations

from itertools import count, starmap
from typing import Iterable, Iterator

from more_itertools import unzip
from termcolor import colored

from frontend.src.utils import output
from frontend.src.utils.output.percentual_indenting import column_percentual_indentation, IndentedPrint


class OptionCollection(dict):
    def __init__(self, keyword_2_description_and_function):
        descriptions, functions = unzip(keyword_2_description_and_function.values())

        super().__init__(dict(zip(keyword_2_description_and_function, functions)))

        self._information_rows: Iterator[str] = self._get_information_rows(
            keyword_description_pairs=zip(
                keyword_2_description_and_function,
                descriptions
            )
        )

    @staticmethod
    def _get_information_rows(keyword_description_pairs: Iterable[tuple[str, str]]) -> Iterator[str]:
        return iter(
            output.align(
                *map(  # type: ignore
                    list,  # type: ignore
                    unzip(
                        starmap(
                            lambda keyword, instruction: (
                                colored(keyword, 'red'),
                                instruction
                            ),
                            keyword_description_pairs
                        )
                    )
                )
            )
        )

    def display_instructions(self, row_index_2_insertion_string: dict[int, str] | None = None):
        if not row_index_2_insertion_string:
            row_index_2_insertion_string = {}

        _print = IndentedPrint(indentation=column_percentual_indentation(0.35))

        _print('Enter:')

        for i in count(0, step=1):
            if (string := row_index_2_insertion_string.get(i)) is not None:
                output.centered(f'\n{string}\n')
            else:
                try:
                    _print(f'    {next(self._information_rows)}')
                except StopIteration:
                    break

        output.empty_row()