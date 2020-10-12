from typing import Optional, List, Iterator
import random
from collections.abc import Mapping

from lingularity.backend.metadata import (
    ReplacementForenames,
    get_replacement_forenames,
    language_metadata,
    DefaultForenamesTranslations
)


DEFAULT_FORENAMES = ('Tom', 'John', 'Mary', 'Alice')
_DEFAULT_SURNAME = 'Jackson'


class ForenameConvertor:
    def __init__(self, language: str, train_english: bool):
        replacement_forenames: Optional[ReplacementForenames] = get_replacement_forenames(language)

        self._forenames_convertible: bool = bool(replacement_forenames)
        self._train_english: bool = train_english
        self._default_forename_translations: Optional[DefaultForenamesTranslations] = language_metadata[language]['translations']['defaultForenames']

        self._replacement_forenames: Optional[List[List[List[str]]]] = None
        self.demonym: Optional[str] = None

        if replacement_forenames is not None:
            self.demonym = replacement_forenames['demonym']
            self._replacement_forenames = [list(gender_dict.values()) for gender_dict in replacement_forenames.values() if issubclass(Mapping, gender_dict)]

    def __call__(self, sentence_pair: List[str]) -> List[str]:
        if self._forenames_convertible:
            picked_forename_indices: List[Optional[int]] = [None] * len(DEFAULT_FORENAMES)
            for i, sentence in enumerate(sentence_pair):
                sentence_pair[i] = self._convert_sentence(sentence, is_english_sentence=not i, replacement_forename_indices=picked_forename_indices)
        return sentence_pair

    def _convert_sentence(self, sentence: str, is_english_sentence: bool, replacement_forename_indices: List[Optional[int]]) -> str:
        spelling_index = int(not is_english_sentence)

        fragments = sentence.split(' ')
        for gender_index, default_name in enumerate([DEFAULT_FORENAMES, self._default_forename_translations][spelling_index]):
            for i, (fragment, convert) in enumerate(zip(fragments, self._forename_conversion_mask(fragments, default_name, is_english_sentence))):
                if convert:
                    if replacement_forename_indices[gender_index] is None:
                        replacement_forename_indices[gender_index] = random.choice(range(len(self._replacement_forenames[gender_index][spelling_index])))
                    fragments[i] = fragment.replace(default_name, self._replacement_forenames[gender_index][spelling_index][replacement_forename_indices[gender_index]])

        return ' '.join(fragments)

    @staticmethod
    def _forename_conversion_mask(sentence_fragments: List[str], forename: str, is_english_sentence: bool) -> Iterator[bool]:
        for fragment in sentence_fragments:
            if forename in fragment and (not is_english_sentence or is_english_sentence and all(not char.isalpha() for char in fragment.replace(forename, ''))):
                yield True
            else:
                yield False


if __name__ == '__main__':
    converter = ForenameConvertor('Italian', train_english=False)
    print(converter(["Tomorrow Tom will freakin' school these fools, which will astonish Mary.", "Tomorrow Tom will freakin' school these fools"]))
