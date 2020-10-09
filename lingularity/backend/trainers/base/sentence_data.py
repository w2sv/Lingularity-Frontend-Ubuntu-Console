import os
from functools import cached_property
from typing import Optional, List, Iterator, Iterable, Set
from collections import Counter
from itertools import chain, islice
from bisect import insort

import numpy as np
from more_itertools import unzip
from textacy.similarity import levenshtein
from tqdm import tqdm

from lingularity.backend.ops.data_mining.downloading import download_sentence_data
from lingularity.backend import BASE_LANGUAGE_DATA_PATH
from lingularity.backend.utils.strings import get_meaningful_tokens, is_of_latin_script, strip_special_characters, find_common_start
from lingularity.backend.utils.iterables import windowed, longest_value


class SentenceData(np.ndarray):
    """ Abstraction of sentence pair data

        equals np.ndarray[List[List[str]], i.e. ndim == 2,
        with, in case of _train_english being True:
            SentenceData[:, 0] = english sentences,
            SentenceData[:, 1] = translations
        otherwise vice-versa """

    _train_english: bool = None

    def __new__(cls, language: str, train_english=False):
        """ Downloads sentence data if necessary """

        cls._train_english = train_english

        # download sentence data if necessary
        if not os.path.exists((language_dir_path := f'{BASE_LANGUAGE_DATA_PATH}/{language}')):
            download_sentence_data(language=language)

        return cls._read_in(language_dir_path, train_english).view(SentenceData)

    @staticmethod
    def _read_in(language_dir_path: str, train_english: bool) -> np.ndarray:
        processed_sentence_data = []
        with open(f'{language_dir_path}/sentence_data.txt', 'r', encoding='utf-8') as sentence_data_file:
            for sentence_pair_line in sentence_data_file.readlines():
                sentence_pair = sentence_pair_line.strip('\n').split('\t')
                if train_english:
                    sentence_pair = list(reversed(sentence_pair))
                processed_sentence_data.append(sentence_pair)

        return np.asarray(processed_sentence_data)

    # -------------------
    # Translation query
    # -------------------
    def query_translation(self, english_sentence: str, file_max_length_percentage: float = 1.0) -> Optional[str]:
        """
            Args:
                 english_sentence: complete phrase including punctuation whose translation ought to be queried
                 file_max_length_percentage: percentage of sentence_data file length after exceeding which
                    the query process will be stopped for performance optimization purposes """

        for content, i in ((sentence_pair[0], i) for i, sentence_pair in
                           enumerate(self[:int(len(self) * file_max_length_percentage)])):
            if content == english_sentence:
                return self[i][1]
        return None

    # -------------------
    # Translation(s) deduction
    # -------------------
    def deduce_forename_translations(self, forename: str) -> List[str]:
        if self.foreign_language_sentences.uses_latin_script:
            return self._deduce_forename_translations_latin_script_language(forename)
        return self._deduce_forename_translations_non_latin_script_language(forename)

    def _deduce_forename_translations_latin_script_language(self, forename: str) -> List[str]:
        candidates_2_occurrences = Counter()

        for english_sentence, foreign_language_sentence in zip(self.english_sentences, self.foreign_language_sentences):
            if forename in get_meaningful_tokens(english_sentence, apostrophe_splitting=True):
                for title_word in filter(lambda token: token.istitle(), get_meaningful_tokens(foreign_language_sentence, apostrophe_splitting=True)):
                    candidates_2_occurrences[title_word] += 1

                # return most common candidate if corresponding occurrences > 200% of sum(max_occurrences[1:4])
                if len(candidates_2_occurrences) >= 4:
                    most_common_candidates, occurrences = unzip(candidates_2_occurrences.most_common(4))
                    if next(occurrences) / sum(occurrences) >= 2.0:
                        return [next(most_common_candidates)]

        filtered_candidates = []
        for candidate, occurrences in candidates_2_occurrences.most_common():
            if levenshtein(forename, candidate) >= 0.4:
                if all(levenshtein_score <= 0.6 for levenshtein_score in map(lambda filtered_candidate: levenshtein(filtered_candidate, candidate), filtered_candidates)):
                    filtered_candidates.append(candidate)

        return filtered_candidates

    def _deduce_forename_translations_non_latin_script_language(self, forename: str) -> List[str]:
        def continuous_substrings(string: str, lengths: Optional[Iterable[int]] = None) -> Iterator[str]:
            """
                Args:
                    string: string to extract substrings from
                    lengths: Iterable of desired substring lengths,
                        may contain lengths > len(string) which will be automatically ignored

                Returns:
                    Iterator of entirety of continuous substrings of min length = 2 comprised by string
                    sorted with respect to their lengths, e.g.:
                        continuous_substrings('path') -> Iterator[
                            'pa', 'at', 'th',
                            'pat', 'ath',
                            'path'
                        ] """

            if lengths is None:
                lengths = range(2, len(string) + 1)
            else:
                lengths = filter(lambda val: val > 1, lengths)

            return map(''.join, chain.from_iterable(map(lambda length: windowed(string, length), lengths)))

        translation_candidates, translation_lengths = (set() for _ in range(2))
        forename_comprising_sentence_substrings_cache: List[Set[str]] = []
        for english_sentence, foreign_language_sentence in tqdm(zip(self.english_sentences, self.foreign_language_sentences)):
            if forename in get_meaningful_tokens(english_sentence, apostrophe_splitting=True):
                foreign_language_sentence = strip_special_characters(foreign_language_sentence, include_dash=True, include_apostrophe=True)

                # skip sentences possessing substring already being confirmed as substring
                if len((intersection := translation_candidates.intersection(continuous_substrings(foreign_language_sentence, lengths=translation_lengths)))):
                    print(translation_candidates, intersection)
                    continue

                sentence_substrings = set(continuous_substrings(foreign_language_sentence))
                for i, forename_comprising_sentence_substrings in enumerate(forename_comprising_sentence_substrings_cache):
                    if len((substring_intersection := sentence_substrings.intersection(forename_comprising_sentence_substrings))):
                        forename_translation = sorted(substring_intersection, key=len, reverse=True)[0]
                        translation_candidates.add(forename_translation)
                        translation_lengths.add(len(forename_translation))

                        del forename_comprising_sentence_substrings_cache[i]
                        break
                else:
                    forename_comprising_sentence_substrings_cache.append(sentence_substrings)

        return list(translation_candidates)

    def _strip_overlaps(self, sorted_candidate_list: List[str]):
        for i, candidate in enumerate(sorted_candidate_list):
            longest_overlap = longest_value(map(find_common_start, *islice(sorted_candidate_list, i+1, None)))
            if len(longest_overlap):
                stripped_candidate_list = list(filter(lambda candidate: longest_overlap not in candidate, sorted_candidate_list))
                insort(stripped_candidate_list, longest_overlap)
                return self.strip_overlaps(stripped_candidate_list)
        return sorted_candidate_list

    # -------------------
    # Columns
    # -------------------
    class Column(np.ndarray):
        """ Abstraction of entirety of sentence data pertaining to one language

            equals: np.ndarray[List[str]] """

        def __new__(cls, sentence_data_column: np.ndarray):
            return sentence_data_column.view(SentenceData.Column)

        @cached_property
        def uses_latin_script(self) -> bool:
            return is_of_latin_script(self[-1], trim=True)

        def comprises_tokens(self, query_tokens: List[str], query_length_percentage=1.0) -> bool:
            """ Args:
                    query_tokens: tokens which have to be comprised by sentence data in order for method to
                        return True
                    query_length_percentage: sentence data max length up to which presence of query tokens will be
                        queried """

            # return False if query tokens of different script type than sentences
            if self.uses_latin_script != is_of_latin_script(''.join(query_tokens), trim=False):
                return False

            query_tokens_set = set(query_tokens)
            for sentence in self[:int(len(self) * query_length_percentage)]:
                meaningful_tokens = get_meaningful_tokens(sentence, apostrophe_splitting=False)
                query_tokens_set -= meaningful_tokens
                if not len(query_tokens_set):
                    return True
            return False

    @cached_property
    def english_sentences(self) -> Column:
        return self.Column(self[:, 0 + int(self._train_english)])

    @cached_property
    def foreign_language_sentences(self) -> Column:
        return self.Column(self[:, 1 - int(self._train_english)])


if __name__ == '__main__':
    s = SentenceData('Chinese')

    translation = s.deduce_forename_translations('Tom')
    print(translation)

    translation = s.deduce_forename_translations('Mary')
    print(translation)