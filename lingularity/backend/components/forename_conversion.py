from typing import Optional, List, Iterator, Tuple, Iterable
import random
from collections.abc import Mapping

from lingularity.backend.resources import strings as string_resources
from lingularity.backend.utils.strings import split_multiple
from lingularity.backend.metadata import (
    SubstitutionForenamesMap,
    get_substitution_forenames_map,
    language_metadata,
    replacement_forenames_available_for
)


DEFAULT_FORENAMES = ('Tom', 'John', 'Mary', 'Alice')  # _DEFAULT_SURNAME = 'Jackson'


class ForenameConvertor:
    @staticmethod
    def available_for(language: str) -> bool:
        return replacement_forenames_available_for(language)

    def __init__(self, language: str, train_english: bool):
        """ Assumes previous assertion of language convertibility  """

        self._train_english: bool = train_english

        substitution_forenames_map: SubstitutionForenamesMap = get_substitution_forenames_map([language, string_resources.ENGLISH][train_english])

        self.demonym: Optional[str] = substitution_forenames_map['demonym']
        self.country: str = substitution_forenames_map['country']
        self._replacement_forenames: List[List[List[str]]] = self._unmap_replacement_forenames(substitution_forenames_map)

        self._default_forename_translations: List[List[str]] = self._unmap_default_forename_translations(language)
        self._uses_latin_script: bool = language_metadata[language]['properties']['usesLatinScript']

    @staticmethod
    def _unmap_replacement_forenames(substitution_forenames_map: SubstitutionForenamesMap) -> List[List[List[str]]]:
        """ Returns:
                3D list with:
                    1st dim: [male_forenames, female_forenames],
                    2nd dim: [latin_spelling, native_spelling],
                    3rd dim: [replacement_forename_1, replacement_forename_2, ..., replacement_forename_n] """

        return [list(gender_dict.values()) for gender_dict in substitution_forenames_map.values() if isinstance(gender_dict, Mapping)]

    @staticmethod
    def _unmap_default_forename_translations(language: str) -> List[List[str]]:
        """ Returns:
                2D list with:
                    1st dim: [Tom, John, Mary, Alice]
                    2nd dim: [translation_1, translation_2, ..., translation_n] """

        return list(map(list, language_metadata[language]['translations']['defaultForenames'].values()))  # type: ignore

    def __call__(self, sentence_pair: List[str]) -> List[str]:

        # invert order of sentence pair in order to line indices up with those of
        # replacement forenames, default forename translations in case of English training
        if self._train_english:
            return list(reversed(self._convert_sentence_pair(reversed(sentence_pair))))
        else:
            return self._convert_sentence_pair(sentence_pair)

    def _convert_sentence_pair(self, sentence_pair: Iterable[str]) -> List[str]:
        forename_index_blacklist: List[Optional[int]] = [None, None]  # for prevention of usage of same replacement
        # forename for two different default forenames of same gender

        sentence_pair_fragments: List[List[str]] = [sentence.split(' ') for sentence in sentence_pair]

        # iterate over contained forename pairs
        for forename_pair, is_female in self._contained_default_forename_pairs_with_gender(sentence_pair_fragments):
            replacement_forename_index: Optional[int] = None

            # iterate over sentence pair
            for is_foreign_language, fragments in enumerate(sentence_pair_fragments):
                default_forename = forename_pair[is_foreign_language]

                fragment_conversion_mask = self._forename_containment_mask(default_forename, fragments, bool(is_foreign_language))
                replacement_forenames = self._replacement_forenames[is_female][is_foreign_language and not self._uses_latin_script]

                # iterate over sentence fragments
                for fragment_index, (contains_default_forename, fragment) in enumerate(zip(fragment_conversion_mask, fragments)):
                    if contains_default_forename:
                        if replacement_forename_index is None:
                            replacement_forename_index = self._draw_forename_index(len(replacement_forenames), banned_index=forename_index_blacklist[is_female])
                            forename_index_blacklist[is_female] = replacement_forename_index
                        fragments[fragment_index] = fragment.replace(default_forename, replacement_forenames[replacement_forename_index])

                sentence_pair_fragments[is_foreign_language] = fragments

        return [' '.join(sentence_fragments) for sentence_fragments in sentence_pair_fragments]

    @staticmethod
    def _draw_forename_index(n_drawable_forenames: int, banned_index: Optional[int]) -> int:
        drawable_indices = list(range(n_drawable_forenames))
        if banned_index is not None:
            drawable_indices.remove(banned_index)

        return random.choice(drawable_indices)

    def _contained_default_forename_pairs_with_gender(self, sentence_pair_fragments: List[List[str]]) -> Iterator[Tuple[Tuple[str, str], bool]]:
        """ Returns:
                Iterator of
                    default forename pairs contained in sentence pair fragments: Tuple[str, str]
                        first of which is the english forename, second the corresponding foreign language translation_field
                    with corresponding is_female_forename flag: bool

            >>> sentence_pair_fragments = [['Tom', 'ate', 'Marys', 'tuna.'], ['Tomás', 'mangiava', 'il', 'tonno', 'de', 'Maria.']]
            >>> list(ForenameConvertor('Italian', train_english=False)._contained_default_forename_pairs_with_gender(sentence_pair_fragments))
            [(('Tom', 'Tomás'), False), (('Mary', 'Maria'), True)]
            """

        for forename_index, (default_forename, forename_translations) in enumerate(zip(DEFAULT_FORENAMES, self._default_forename_translations)):
            if self._forename_comprised_by_fragments(default_forename, sentence_pair_fragments[0], is_foreign_language_sentence=False):
                for forename_translation in forename_translations:
                    if self._forename_comprised_by_fragments(forename_translation, sentence_pair_fragments[1], is_foreign_language_sentence=True):
                        yield (default_forename, forename_translation), forename_index >= 2
                        break

    @staticmethod
    def _forename_comprised_by_fragments(
            forename: str,
            fragments: List[str],
            is_foreign_language_sentence: bool) -> bool:

        return any(ForenameConvertor._forename_containment_mask(forename, fragments, is_foreign_language_sentence))

    @staticmethod
    def _forename_containment_mask(
            forename: str,
            fragments: List[str],
            is_foreign_language_sentence: bool) -> Iterator[bool]:

        """ Returns:
                boolean mask of length of fragments whose elements represent whether or not
                the respective fragments contain the passed forename and are hence to be converted

                >>> list(ForenameConvertor._forename_containment_mask('Tom', ["Tom's", "seriously", "messed", "up."], False))
                [True, False, False, False]
                >>> list(ForenameConvertor._forename_containment_mask('Tom', ["Tomorrow", "Mary", "sacrifices", "Toms", "virginity?"], False))
                [False, False, False, True, False]
                """

        for fragment in fragments:
            yield forename in fragment and (is_foreign_language_sentence or ForenameConvertor._contains_english_forename(fragment, forename))

    @staticmethod
    def _contains_english_forename(english_fragment: str, forename: str) -> bool:
        def is_s_trailed_forename() -> bool:
            return english_fragment[:-1] == forename and english_fragment[-1] == 's'

        def is_special_character_delimited_forename() -> bool:
            return split_multiple(english_fragment, delimiters=list("'?!.,"))[0] == forename

        return is_s_trailed_forename() or is_special_character_delimited_forename()


if __name__ == '__main__':
    sps = [
        ["Ask Tom.", "去问汤姆"],
        ["Mary came in.", "瑪麗進來了。"],
        ["Tom hugged Mary.", "汤姆拥抱了玛丽"],
        ["Tom is ecstatic.", "汤姆兴奋不已。"],
        ["Mary doesn't wear as much makeup as Alice.", "玛丽没有化爱丽丝那样浓的妆。"],
        ["I don't believe Tom's version of the story.", "我不相信汤姆的说法。"]
    ]

    from time import time

    converter = ForenameConvertor('Chinese', train_english=False)

    for sp in sps:
        t1 = time()
        random.seed(69)
        res = converter(sp)
        print(res, time() - t1)
