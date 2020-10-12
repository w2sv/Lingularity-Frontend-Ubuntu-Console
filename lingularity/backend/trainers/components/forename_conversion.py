from typing import Optional, List, Iterator, Sequence, Iterable
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
        replacement_forenames_map: Optional[ReplacementForenames] = get_replacement_forenames(language)

        self.demonym: Optional[str] = None

        self._replacement_forenames: List[List[List[str]]]
        if replacement_forenames_map is not None:
            self.demonym = replacement_forenames_map['demonym']
            self._replacement_forenames = [list(gender_dict.values()) for gender_dict in replacement_forenames_map.values() if isinstance(gender_dict, Mapping)]

        self._forenames_convertible: bool = bool(replacement_forenames_map)
        self._train_english: bool = train_english
        self._default_forename_translations: List[List[str]]

        if (default_forename_translations := language_metadata[language]['translations']['defaultForenames']) is not None:
            self._default_forename_translations = list(map(list, default_forename_translations.values()))  # type: ignore

        self._uses_latin_script: bool = language_metadata[language]['properties']['usesLatinScript']

    def __call__(self, sentence_pair: List[str]) -> List[str]:
        if self._forenames_convertible:
            if self._train_english:
                sentence_pair = list(reversed(self._convert_sentence_pair(reversed(sentence_pair))))
            else:
                sentence_pair = self._convert_sentence_pair(sentence_pair)
        return sentence_pair

    def _convert_sentence_pair(self, sentence_pair: Iterable[str]) -> List[str]:
        used_replacement_forename_indices: List[Optional[int]] = [None, None]

        sentence_pair_fragments: List[List[str]] = [sentence.split(' ') for sentence in sentence_pair]
        forenames: List[Sequence[Optional[str]]] = [DEFAULT_FORENAMES, self._present_forename_translations(sentence_pair_fragments)]

        for default_forename_index, to_be_converted in enumerate(map(bool, forenames[1])):
            if to_be_converted:
                replacement_forename_index: Optional[int] = None

                for foreign_language_index, fragments in enumerate(sentence_pair_fragments):
                    assert (default_forename := forenames[foreign_language_index][default_forename_index]) is not None

                    fragment_conversion_mask = self._fragment_conversion_mask(default_forename, fragments, bool(foreign_language_index))

                    for fragment_index, (fragment, convert) in enumerate(zip(fragments, fragment_conversion_mask)):
                        if convert:
                            gender_index = default_forename_index // 2
                            script_index = foreign_language_index and not self._uses_latin_script
                            gender_script_corresponding_replacement_forenames: List[str] = self._replacement_forenames[gender_index][script_index]

                            if replacement_forename_index is None:
                                replacement_forename_index = random.choice(list(filter(lambda _forename_index: used_replacement_forename_indices[gender_index] != _forename_index, range(len(gender_script_corresponding_replacement_forenames)))))
                                used_replacement_forename_indices[gender_index] = replacement_forename_index
                            sentence_pair_fragments[foreign_language_index][fragment_index] = fragment.replace(default_forename, gender_script_corresponding_replacement_forenames[replacement_forename_index])

        return [' '.join(sentence_fragments) for sentence_fragments in sentence_pair_fragments]

    def _present_forename_translations(self, sentence_pair_fragments: List[List[str]]) -> List[Optional[str]]:
        present_forename_translations: List[Optional[str]] = [None] * len(DEFAULT_FORENAMES)
        for forename_index, (default_forename, forename_translations) in enumerate(zip(DEFAULT_FORENAMES, self._default_forename_translations)):
            if self._forename_comprised_by_fragments(default_forename, sentence_pair_fragments[0], is_foreign_language_sentence=False):
                for forename_translation in forename_translations:
                    if self._forename_comprised_by_fragments(forename_translation, sentence_pair_fragments[1], is_foreign_language_sentence=True):
                        present_forename_translations[forename_index] = forename_translation
                        break

        return present_forename_translations

    @staticmethod
    def _forename_comprised_by_fragments(forename: str, fragments: List[str], is_foreign_language_sentence: bool) -> bool:
        return any(ForenameConvertor._fragment_conversion_mask(forename, fragments, is_foreign_language_sentence=is_foreign_language_sentence))

    @staticmethod
    def _fragment_conversion_mask(forename: str, sentence_fragments: List[str], is_foreign_language_sentence: bool) -> Iterator[bool]:
        for fragment in sentence_fragments:
            if forename in fragment and (is_foreign_language_sentence or all(not char.isalpha() for char in fragment.replace(forename, ''))):
                yield True
            else:
                yield False


if __name__ == '__main__':
    sentence_pair = [
        "Tomorrow Tom will freakin' school these fools, which will astonish Mary. John approved of that, which fascinated Alice.",
        "Domani Tom andrà a scuola con questi pazzi, che stupiranno Maria. John l'ha approvato, che affascinava Alice."
    ]

    print(ForenameConvertor('Italian', train_english=True).__call__(sentence_pair))
