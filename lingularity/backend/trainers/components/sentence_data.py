from typing import Optional, List, Set, Callable, Iterable, Counter, Iterator, Tuple
import os
from functools import cached_property
import collections

from tqdm import tqdm
import numpy as np
from textacy.similarity import levenshtein

from lingularity.backend import sentence_data_path
from lingularity.backend.ops.data_mining.downloading import download_sentence_data
from lingularity.backend.trainers.components.forename_conversion import DEFAULT_FORENAMES
from lingularity.backend.utils.iterables import longest_value
from lingularity.backend.utils.strings import (
    get_unique_meaningful_tokens,
    is_of_latin_script,
    strip_special_characters,
    continuous_substrings,
    longest_continuous_partial_overlap,
    strip_unicode
)


class SentenceData(np.ndarray):
    """ Abstraction of sentence pair data

        equals np.ndarray[List[List[str]], i.e. ndim == 2,
        with, in case of _train_english being False:
            SentenceData[:, 0] = english sentences,
            SentenceData[:, 1] = translations
        otherwise vice-versa """

    _train_english: bool = False

    def __new__(cls, language: str, train_english=False):
        """ Downloads sentence data if necessary """

        cls._train_english = train_english

        # download sentence data if necessary
        if not os.path.exists((_sentence_data_path := sentence_data_path(language))):
            download_sentence_data(language=language)

        return cls._read_in(_sentence_data_path, train_english).view(SentenceData)

    @staticmethod
    def _read_in(_sentence_data_path: str, train_english: bool) -> np.ndarray:
        processed_sentence_data = []
        with open(_sentence_data_path, 'r', encoding='utf-8', errors='strict') as sentence_data_file:
            for sentence_pair_line in sentence_data_file.readlines():
                sentence_pair = strip_unicode(sentence_pair_line[:-1]).split('\t')
                if train_english:
                    sentence_pair = list(reversed(sentence_pair))
                processed_sentence_data.append(sentence_pair)

        return np.asarray(processed_sentence_data)

    # -------------------
    # Columns
    # -------------------
    class Column(np.ndarray):
        """ Abstraction of entirety of sentence data pertaining to one language

            equals: np.ndarray[str] """

        def __new__(cls, sentence_data_column: np.ndarray):
            return sentence_data_column.view(SentenceData.Column)

        @cached_property
        def uses_latin_script(self) -> bool:
            return is_of_latin_script(self[-1], remove_non_alphabetic_characters=True)

        def comprises_tokens(self, query_tokens: List[str], query_length_percentage=1.0) -> bool:
            """ Args:
                    query_tokens: tokens which have to be comprised by sentence data in order for method to
                        return True
                    query_length_percentage: sentence data max length up to which presence of query tokens will be
                        queried """

            # return False if query tokens of different script type than sentences
            if self.uses_latin_script != is_of_latin_script(''.join(query_tokens),
                                                            remove_non_alphabetic_characters=False):
                return False

            query_tokens_set = set(query_tokens)
            for sentence in self[:int(len(self) * query_length_percentage)]:
                meaningful_tokens = get_unique_meaningful_tokens(sentence, apostrophe_splitting=False)
                query_tokens_set -= meaningful_tokens
                if not len(query_tokens_set):
                    return True
            return False

        @cached_property
        def comprising_characters(self) -> Set[str]:
            characters = set()

            for sentence in self:
                characters.update(set(list(sentence)))

            return characters

    @cached_property
    def english_sentences(self) -> Column:
        return self.Column(self[:, 0 + int(self._train_english)])

    @cached_property
    def foreign_language_sentences(self) -> Column:
        return self.Column(self[:, 1 - int(self._train_english)])

    # -------------------
    # Translation query
    # -------------------
    def query_translation(self, english_sentence: str, file_max_length_percentage: float = 1.0) -> Optional[str]:
        """
            Args:
                 english_sentence: complete phrase including punctuation whose translation_field ought to be queried
                 file_max_length_percentage: percentage of sentence_data file length after exceeding which
                    the query process will be stopped for performance optimization purposes """

        for content, i in ((sentence_pair[0], i) for i, sentence_pair in
                           enumerate(self[:int(len(self) * file_max_length_percentage)])):
            if content == english_sentence:
                return self[i][1]
        return None

    # -------------------
    # Deduction
    # -------------------

    # -------------------
    # .Proper Nouns
    # -------------------
    def deduce_proper_nouns(self) -> Set[str]:
        """ Working principle:
                for each sentence pair:
                    - get set of intersection between tokens of english sentence and its translation_field
                    - add tokens starting on uppercase character being either comprised of at least 2 characters or
                      non-latin

            Returns:
                set of lowercase proper nouns """

        proper_nouns = set()

        print('Procuring proper nouns...')
        for sentence_pair in tqdm(self):
            proper_noun_candidates = set.intersection(*map(get_unique_meaningful_tokens, sentence_pair))
            for candidate in proper_noun_candidates:
                if candidate.istitle() and len(candidate) > 1:
                    proper_nouns.add(candidate.lower())

        return proper_nouns

    # -------------------
    # .Forename Translations
    # -------------------
    def deduce_forename_translations(self) -> List[Set[str]]:
        candidates_list: List[Set[str]] = []

        for default_forename in DEFAULT_FORENAMES:
            candidates_list.append(self._deduce_proper_noun_translation(default_forename))

        for i, candidates in enumerate(candidates_list):
            for candidate in candidates:
                for j, alternating_forename_candidates in enumerate(candidates_list):
                    if i != j:
                        candidates_list[j] = set(filter(lambda alternating_forename_candidate: candidate not in alternating_forename_candidate, alternating_forename_candidates))

        return candidates_list

    @property
    def _deduce_proper_noun_translation(self) -> Callable[[str], Set[str]]:
        if self.foreign_language_sentences.uses_latin_script:
            return self._deduce_proper_noun_translations_latin_script_language
        return self._deduce_proper_noun_translations_non_latin_script_language

    def _deduce_proper_noun_translations_latin_script_language(self, proper_noun: str) -> Set[str]:
        MIN_CANDIDATE_PN_LEVENSHTEIN = 0.5
        MAX_FILTERED_CANDIDATE_CONFIRMED_TRANSLATION_LEVENSHTEIN = 0.8

        candidates = set()
        lowercase_words_cache = set()

        for english_sentence, foreign_language_sentence in self._english_to_foreign_language_sentence_iterator:
            if proper_noun in get_unique_meaningful_tokens(english_sentence, apostrophe_splitting=True):
                for token in get_unique_meaningful_tokens(foreign_language_sentence, apostrophe_splitting=True):
                    if token.istitle() and levenshtein(proper_noun, token) >= MIN_CANDIDATE_PN_LEVENSHTEIN:
                        candidates.add(token)
                    elif token.islower():
                        lowercase_words_cache.add(token)

        filtered_candidates: Set[str] = set()
        for candidate in filter(lambda candidate: candidate.lower() not in lowercase_words_cache, candidates):
            if all(levenshtein_score <= MAX_FILTERED_CANDIDATE_CONFIRMED_TRANSLATION_LEVENSHTEIN for levenshtein_score in map(lambda filtered_candidate: levenshtein(filtered_candidate, candidate), filtered_candidates)):
                filtered_candidates.add(candidate)

        return filtered_candidates

    def _deduce_proper_noun_translations_non_latin_script_language(self, proper_noun: str) -> Set[str]:
        CANDIDATE_BAN_INDICATION = -1
        MIN_CANDIDATE_CONFIRMATION_OCCURRENCE = 20
        MAGIC_NUMBER = 3

        translation_candidates: Set[str] = set()
        translation_candidate_2_n_occurrences: Counter[str] = collections.Counter()
        translation_comprising_sentence_substrings_cache: List[Set[str]] = []
        for english_sentence, foreign_language_sentence in self._english_to_foreign_language_sentence_iterator:
            if proper_noun in get_unique_meaningful_tokens(english_sentence, apostrophe_splitting=True):
                foreign_language_sentence = strip_special_characters(foreign_language_sentence, include_dash=True, include_apostrophe=True).replace(' ', '')

                # skip sentences possessing substring already being present in candidates list
                if len((intersections := translation_candidates.intersection(continuous_substrings(foreign_language_sentence, lengths=set(map(len, translation_candidates)))))):
                    for intersection in intersections:
                        translation_candidate_2_n_occurrences[intersection] += 1

                    if len(intersections) > 1:
                        n_occurrences: List[int] = list(map(translation_candidate_2_n_occurrences.get, intersections))  # type: ignore
                        if any(occurrence >= MIN_CANDIDATE_CONFIRMATION_OCCURRENCE for occurrence in n_occurrences):
                            for n_occurrence, candidate in zip(n_occurrences, intersections):
                                if n_occurrence == MAGIC_NUMBER:
                                    translation_candidates.remove(candidate)
                                    translation_candidate_2_n_occurrences[candidate] = CANDIDATE_BAN_INDICATION

                else:
                    sentence_substrings = set(continuous_substrings(foreign_language_sentence))
                    for i, forename_comprising_sentence_substrings in enumerate(translation_comprising_sentence_substrings_cache):
                        if len((substring_intersection := sentence_substrings.intersection(forename_comprising_sentence_substrings))):
                            forename_translation = longest_value(substring_intersection)
                            if translation_candidate_2_n_occurrences[forename_translation] != CANDIDATE_BAN_INDICATION:
                                translation_candidates.add(forename_translation)
                                translation_candidate_2_n_occurrences[forename_translation] += 1

                                del translation_comprising_sentence_substrings_cache[i]
                                break
                    else:
                        translation_comprising_sentence_substrings_cache.append(sentence_substrings)

        return self._strip_overlaps(translation_candidates)

    @property
    def _english_to_foreign_language_sentence_iterator(self) -> Iterator[Tuple[str, str]]:
        return zip(self.english_sentences, self.foreign_language_sentences)

    @staticmethod
    def _strip_overlaps(translation_candidates: Iterable[str]) -> Set[str]:
        if longest_partial_overlap := longest_continuous_partial_overlap(translation_candidates, min_length=2):
            return SentenceData._strip_overlaps(list(filter(lambda candidate: longest_partial_overlap not in candidate, translation_candidates)) + [longest_partial_overlap])  # type: ignore
        return set(translation_candidates)


if __name__ == '__main__':
    from time import time

    # t1 = time()
    # translations = SentenceData('Hebrew').deduce_forename_translations()
    # print(translations)
    # print(time() - t1)

    s = SentenceData('Hungarian')
    print(s.foreign_language_sentences.comprising_characters)
    print(s.english_sentences.comprising_characters)
