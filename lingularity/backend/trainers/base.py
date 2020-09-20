from typing import List, Optional, Iterator, Any, Sequence, Tuple, Dict
import os
from abc import ABC
import time
import random

import numpy as np
import gtts
import vlc
from mutagen.mp3 import MP3

from lingularity.backend.database import MongoDBClient
from lingularity.backend.data_fetching.scraping.language_typical_forenames import scrape_language_typical_forenames
from lingularity.backend.data_fetching.scraping.demonyms import scrape_demonyms
from lingularity.backend.ops import google
from lingularity.backend.utils.time import get_timestamp
from lingularity.backend.trainers.token_maps import (UnnormalizedToken2SentenceIndices, Stem2SentenceIndices,
                                                     Lemma2SentenceIndices, Token2SentenceIndicesMap)


class TrainerBackend(ABC):
    _BASE_LANGUAGE_DATA_PATH = f'{os.getcwd()}/language_data'
    _TTS_AUDIO_FILE_PATH = f'{os.getcwd()}/tts_audio_files'

    _DEFAULT_SENTENCE_DATA_FORENAMES = ('Tom', 'Mary')

    def __init__(self, non_english_language: str, train_english: bool, mongodb_client: MongoDBClient, vocable_expansion_mode=False):
        if not os.path.exists(self._BASE_LANGUAGE_DATA_PATH):
            os.mkdir(self._BASE_LANGUAGE_DATA_PATH)

        self._non_english_language = non_english_language
        self._train_english = train_english

        if not vocable_expansion_mode:
            self._language_typical_forenames, corresponding_country = scrape_language_typical_forenames(non_english_language)
            self.names_convertible: bool = all(variable is not None for variable in [self._language_typical_forenames, corresponding_country])
            if self.names_convertible and (language_demonyms := scrape_demonyms(country_name=corresponding_country)) is not None:  # type: ignore
                # TODO: check whether demonym equals adjective

                print(f'Employing {language_demonyms[0]} names.')

            self._google_ops_language_abbreviation: Optional[str] = google.get_language_abbreviation(self._non_english_language)
            self.tts_available: bool = self._google_ops_language_abbreviation is not None

        mongodb_client.language = non_english_language
        self.mongodb_client = mongodb_client

        self._item_iterator: Optional[Iterator[Any]] = None
        self.lets_go_translation: Optional[str] = None

    @property
    def locally_available_languages(self) -> List[str]:
        return os.listdir(self._BASE_LANGUAGE_DATA_PATH)

    @property
    def train_english(self):
        return self._train_english

    @train_english.setter
    def train_english(self, flag: bool):
        """ creates english dir if necessary """

        assert self._train_english is False, 'train_english not to be changed after being set to True'

        if flag is True and not os.path.exists(self.language_dir_path):
            os.mkdir(self.language_dir_path)
        self._train_english = flag

    @property
    def language(self):
        return self._non_english_language if not self._train_english else 'English'

    @staticmethod
    def _get_item_iterator(item_list: Sequence[Any]) -> Iterator[Any]:
        np.random.shuffle(item_list)
        return iter(item_list)

    def _get_token_2_sentence_indices_map(self, sentence_data: np.ndarray) -> Token2SentenceIndicesMap:
        lowercase_language = self.language.lower()

        if Lemma2SentenceIndices.exists(lowercase_language):
            return Lemma2SentenceIndices.from_file(lowercase_language)
        else:
            for cls in [Lemma2SentenceIndices, Stem2SentenceIndices]:
                if cls.is_available(lowercase_language):
                    return cls(sentence_data, lowercase_language)

        return UnnormalizedToken2SentenceIndices(sentence_data, discard_proper_nouns=True)

    # ----------------
    # Paths
    # ----------------
    @property
    def language_dir_path(self):
        return f'{self._BASE_LANGUAGE_DATA_PATH}/{self.language}'

    @property
    def sentence_file_path(self) -> str:
        return f'{self.language_dir_path}/sentence_data.txt'

    # ----------------
    # Pre Training
    # ----------------
    def _process_sentence_data_file(self) -> Tuple[np.ndarray, Optional[str]]:
        sentence_data = self._read_in_sentence_data()
        return sentence_data, self._query_sentence_data_for_translation("Let's go!", sentence_data, 0.3)

    def _read_in_sentence_data(self) -> np.ndarray:
        """
            Strips newly downloaded data off reference appendices and overrides data file

            Returns:
                ndarray of List[reference_language_sentence, target_language_sentence]
                    with if not self._train_english:
                        reference_language_sentence == English
                    and vice-versa """

        print('Reading in sentence data...')

        raw_data = open(self.sentence_file_path, 'r', encoding='utf-8').readlines()

        # remove reference appendices from source file if newly downloaded and write to file
        reference_appendix_stripped_data = self._get_reference_appendix_stripped_sentence_data(raw_data)

        # split at tab, strip newlines; invert vertical sentence order in case of english training
        tab_split_data: List[List[str]] = []
        for i, row in enumerate(reference_appendix_stripped_data):
            tab_split_data.append(row.strip('\n').split('\t'))

            if self._train_english:
                tab_split_data[i] = list(reversed(tab_split_data[i]))

        return np.asarray(tab_split_data)

    def _get_reference_appendix_stripped_sentence_data(self, raw_data: List[str]) -> List[str]:
        if len(raw_data[0].split('\t')) > 2:
            reference_appendix_stripped_data = ['\t'.join(row.split('\t')[:2]) + '\n' for row in raw_data]

            with open(self.sentence_file_path, 'w', encoding='utf-8') as write_file:
                write_file.writelines(reference_appendix_stripped_data)
            return reference_appendix_stripped_data
        else:
            return raw_data

    @staticmethod
    def _query_sentence_data_for_translation(english_entry: str, sentence_data: np.ndarray, sentence_file_length_percentage: float = 1.0) -> Optional[str]:
        """
            Args:
                 english_entry: complete phrase whose translation ought to be queried
                 sentence_data: tab-split
                 sentence_file_length_percentage: percentage of sentence_data file length after exceeding which
                    the query process will be stopped for performance optimization purposes """

        for content, i in ((sentence_pair[0], i) for i, sentence_pair in enumerate(sentence_data[:int(len(sentence_data) * sentence_file_length_percentage)])):
            if content == english_entry:
                return sentence_data[i][1]
        return None

    # -----------------
    # Training
    # -----------------
    def get_training_item(self) -> Optional[Any]:
        """
            Returns:
                 None in case of depleted iterator """

        assert self._item_iterator is not None

        try:
            return next(self._item_iterator)
        except StopIteration:
            return None

    def convert_sentences_forenames_if_feasible(self, sentences: List[str]) -> Tuple[str, str]:
        """
            Args:
                sentences: [reference_language_sentence, translation]
            Returns:
                converted sentences if forenames convertible and convertible names present in reference_language_sentence,
                otherwise original sentences """

        reference_language_sentence, translation = sentences
        if self.names_convertible and any(
                default_name in reference_language_sentence for default_name in self._DEFAULT_SENTENCE_DATA_FORENAMES):
            reference_language_sentence, picked_names = self._convert_sentence_forenames(reference_language_sentence)
            translation, _ = self._convert_sentence_forenames(translation, picked_names)
        return reference_language_sentence, translation

    def _convert_sentence_forenames(self, sentence: str, names: Optional[List[Optional[str]]]=None) -> Tuple[str, List[Optional[str]]]:
        """ Note: Assertion of self.names_convertible being True to be made before invocation

            Args:
                sentence: comprising default english names to be converted
                names: list of already selected forenames of order [male_forename, female_forename], which,
                            in case of presence, the correspondingly gendered default forename(s) will be
                            replaced by in order to align the converted names of the reference sentence with
                            the ones of the inherent translation sentence

            Picks gender corresponding forenames randomly from self._language_typical_forenames
            Doesn't demand passed sentence to forcibly contain a convertible name. In that case the original sentence
                will be returned

            Returns:
                converted sentence: str
                selected names: List[Optional[str]] """

        # break up sentence into distinct tokens
        sentence_tokens = sentence[:-1].split(' ')

        # strip tokens off post-apostrophe-appendixes and store the latter with corresponding
        # token index
        post_apostrophe_components_with_index: List[Tuple[str, int]] = []
        for i, token in enumerate(sentence_tokens):
            if len((apostrophe_split_token := token.split("'"))) == 2:
                sentence_tokens[i] = apostrophe_split_token[0]
                post_apostrophe_components_with_index.append((apostrophe_split_token[1], i))

        # replace default name with language and gender-corresponding one if existent
        picked_names: List[Optional[str]] = [None, None]
        for gender_index, default_name in enumerate(self._DEFAULT_SENTENCE_DATA_FORENAMES):
            try:
                tokens_replacement_index = sentence_tokens.index(default_name)  # throws ValueError in case of no default name being present

                if names is None:
                    assert self._language_typical_forenames is not None

                    employed_name = random.choice(self._language_typical_forenames[gender_index])
                else:
                    assert names[gender_index] is not None

                    employed_name = names[gender_index]  # type: ignore

                sentence_tokens[tokens_replacement_index] = employed_name
                picked_names[gender_index] = employed_name
            except ValueError:
                pass

        # add post-apostrophe-appendixes back to corresponding tokens
        for post_apostrophe_token, corresponding_sentence_token_index in post_apostrophe_components_with_index:
            sentence_tokens[corresponding_sentence_token_index] += f"'{post_apostrophe_token}"

        # fuse tokens to string, append sentence closing punctuation
        return ' '.join(sentence_tokens) + sentence[-1], picked_names

    # -----------------
    # .TTS
    # -----------------
    def download_tts_audio(self, text: str) -> str:
        audio_file_path = f'{self._TTS_AUDIO_FILE_PATH}/{get_timestamp()}.mp3'

        gtts.gTTS(text, lang=self._google_ops_language_abbreviation).save(audio_file_path)
        return audio_file_path

    @staticmethod
    def play_audio_file(audio_file_path: str, playback_rate=1.0, suspend_program_for_duration=False):
        player = vlc.MediaPlayer(audio_file_path)
        player.set_rate(playback_rate)
        player.play()

        if suspend_program_for_duration:
            duration = MP3(audio_file_path).info.length / playback_rate - 0.2
            start_time = time.time()
            while time.time() - start_time < duration:
                # TODO: let function break on enter stroke by employing threading
                pass

    def clear_tts_audio_file_dir(self):
        for audio_file in os.listdir(self._TTS_AUDIO_FILE_PATH):
            os.remove(f'{self._TTS_AUDIO_FILE_PATH}/{audio_file}')

    # -----------------
    # Post training
    # -----------------
    def insert_session_statistics_into_database(self, n_trained_items: int):
        update_args = (self.__str__(), n_trained_items)

        self.mongodb_client.update_last_session_statistics(*update_args)
        self.mongodb_client.inject_session_statistics(*update_args)

    def __str__(self):
        return self.__class__.__name__[0].lower()
