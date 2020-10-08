import random
from typing import Optional, List, Iterator

from lingularity.backend.metadata import ForenameConversionData, get_forename_conversion_data, language_metadata


DEFAULT_FORENAMES = ('Tom', 'Mary')


class ForenameConvertor:
    def __init__(self, language: str, train_english: bool):
        data: Optional[ForenameConversionData] = get_forename_conversion_data(language)
        self.forenames_convertible: bool = bool(data)

        self._train_english: bool = train_english

        if self.forenames_convertible:
            self.demonym: str = data.pop('demonym')
            self._replacement_forenames: List[List[List[str]]] = [list(spelling_dict.values()) for spelling_dict in data.values()]

        self._employs_non_latin_characters = language_metadata[language]['employsNonLatinCharacters']
        if self._employs_non_latin_characters:
            self._default_forename_transcriptions: List[str] = language_metadata[language]['translations']['defaultForenames']

    def __call__(self, sentence_pair: List[str]) -> List[str]:
        if self.forenames_convertible:
            picked_forename_indices: List[Optional[int]] = [None, None]
            for i, sentence in enumerate(sentence_pair):
                sentence_pair[i] = self._convert_sentence(sentence, is_english_sentence=not i, replacement_forename_indices=picked_forename_indices)
        return sentence_pair

    def _convert_sentence(self, sentence: str, is_english_sentence: bool, replacement_forename_indices: List[Optional[int]]) -> str:
        spelling_index = int(not is_english_sentence and self._employs_non_latin_characters)

        fragments = sentence.split(' ')
        for gender_index, default_name in enumerate([DEFAULT_FORENAMES, self._default_forename_transcriptions][spelling_index]):
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
