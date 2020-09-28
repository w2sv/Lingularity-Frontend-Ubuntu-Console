from typing import List, Optional, Iterator, Any, Sequence, Tuple, Dict
import os
from abc import ABC, abstractmethod
import time
import random

import numpy as np
import vlc
from mutagen.mp3 import MP3

from lingularity.backend.database import MongoDBClient
from lingularity.backend.data_fetching.scraping.language_typical_forenames import scrape_typical_forenames
from lingularity.backend.data_fetching.scraping.demonyms import scrape_demonym
from lingularity.backend.ops.google.tts import GoogleTTS
from lingularity.backend.utils.time import get_timestamp
from lingularity.backend.trainers.token_maps import (UnnormalizedTokenMap, StemMap,
                                                     LemmaMap, TokenMap)


class TrainerBackend(ABC):
    _BASE_LANGUAGE_DATA_PATH = f'{os.getcwd()}/.language_data'
    _TTS_AUDIO_FILE_PATH = f'{os.getcwd()}/.tts_audio_files'

    _DEFAULT_SENTENCE_DATA_FORENAMES = ('Tom', 'Mary')

    def __init__(self, non_english_language: str, train_english: bool, mongodb_client: MongoDBClient):
        if not os.path.exists(self._BASE_LANGUAGE_DATA_PATH):
            os.mkdir(self._BASE_LANGUAGE_DATA_PATH)

        self._non_english_language = non_english_language
        self._train_english = train_english

        mongodb_client.language = non_english_language
        self.mongodb_client = mongodb_client

        self._item_iterator: Optional[Iterator[Any]] = None
        self.lets_go_translation: Optional[str] = None
        self.n_training_items: Optional[int] = None

        # forename converting
        self._language_typical_forenames, corresponding_country = scrape_typical_forenames(non_english_language)
        self.forenames_convertible = self._language_typical_forenames is not None
        self.demonym = scrape_demonym(country_name=corresponding_country) if self.forenames_convertible else None

        # tts
        self._tts_dialect_2_identifier = GoogleTTS().get_dialect_choices(self._non_english_language)
        self.tts_language_varieties = None if self._tts_dialect_2_identifier is None else list(self._tts_dialect_2_identifier.keys())
        self._tts_language_identifier: Optional[str] = self._get_tts_identifier()
        self.tts_available: bool = any([self._tts_dialect_2_identifier, self._tts_language_identifier])

    @property
    def tts_language_identifier_set(self) -> bool:
        return self._tts_language_identifier is not None

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

    @abstractmethod
    def set_item_iterator(self):
        """ sets _item_iterator, n_training_items """
        pass

    @staticmethod
    def _get_item_iterator(item_list: Sequence[Any]) -> Iterator[Any]:
        np.random.shuffle(item_list)
        return iter(item_list)

    def _get_token_map(self, sentence_data: np.ndarray) -> TokenMap:
        lowercase_language = self.language.lower()

        for cls in [LemmaMap, StemMap]:
            if cls.is_available(lowercase_language):  # type: ignore
                return cls(sentence_data, lowercase_language, load_normalizer=str(self) == 'v')

        return UnnormalizedTokenMap(sentence_data)

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
        """ Returns:
                ndarray of List[reference_language_sentence, target_language_sentence]
                    with if not self._train_english:
                        reference_language_sentence == English
                    and vice-versa """

        print('Reading in sentence data...')

        processed_sentence_data = []
        with open(f'{self.language_dir_path}/sentence_data.txt', 'r', encoding='utf-8') as sentence_data_file:
            for sentence_pair_line in sentence_data_file.readlines():
                sentence_pair = sentence_pair_line.strip('\n').split('\t')
                if self._train_english:
                    sentence_pair = list(reversed(sentence_pair))
                processed_sentence_data.append(sentence_pair)

        return np.asarray(processed_sentence_data)

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

    def convert_forenames_if_feasible(self, sentences: List[str]) -> List[str]:
        """
            Args:
                sentences: [reference_language_sentence, translation]
            Returns:
                converted sentences if forenames convertible and convertible names present in reference_language_sentence,
                otherwise original sentences """

        picked_names = None
        if self.forenames_convertible and any(default_name in sentences[0] for default_name in self._DEFAULT_SENTENCE_DATA_FORENAMES):
            for i, sentence in enumerate(sentences):
                sentences[i], picked_names = self._convert_forenames(sentence, picked_names)
        return sentences

    def _convert_forenames(self, sentence: str, replacement_names: Optional[List[Optional[str]]] = None) -> Tuple[str, List[Optional[str]]]:
        """ Note: Assertion of self.forenames_convertible being True to be made before invocation

            Args:
                sentence: comprising default english names to be converted
                replacement_names: list of already selected forenames of order [male_forename, female_forename], which,
                                   in case of presence, the correspondingly gendered default forename(s) will be
                                   replaced by in order to align the converted names of the reference sentence with
                                   the ones of the inherent translation sentence

            Picks gender corresponding forenames randomly from self._language_typical_forenames
            Doesn't demand passed sentence to forcibly contain a convertible name. In that case the original sentence
                will be returned

            Returns:
                converted sentence: str
                selected names: List[Optional[str]] """

        converted_sentence = f'X{sentence}X'
        picked_names: List[Optional[str]] = [None, None]

        for gender_index, default_name in enumerate(self._DEFAULT_SENTENCE_DATA_FORENAMES):
            if len((name_split_parts := converted_sentence.split(default_name))) > 1:
                if replacement_names is None:
                    assert self._language_typical_forenames is not None
                    employed_name = random.choice(self._language_typical_forenames[gender_index])
                else:
                    assert replacement_names[gender_index] is not None
                    employed_name = replacement_names[gender_index]  # type: ignore

                converted_sentence = employed_name.join(name_split_parts)
                picked_names[gender_index] = employed_name

        return converted_sentence[1:-1], picked_names

    # -----------------
    # .TTS
    # -----------------
    def query_tts_enablement(self):
        if not self.tts_available:
            return False
        if (flag := self.mongodb_client.query_tts_enablement()) is None:
            return True
        return flag

    def _get_tts_identifier(self) -> Optional[str]:
        if self._tts_dialect_2_identifier is None:
            return GoogleTTS().get_identifier(self._non_english_language)

        return self.mongodb_client.query_language_variety_identifier()

    def change_tts_dialect(self, dialect: str):
        if self._tts_language_identifier is not None:
            self.mongodb_client.set_language_variety_usage(self._tts_language_identifier, False)

        self._tts_language_identifier = self._tts_dialect_2_identifier[dialect]
        self.mongodb_client.set_language_variety_usage(self._tts_language_identifier, True)

    def get_playback_speed(self) -> Optional[float]:
        if not self.tts_available:
            return None
        else:
            if (preset_playback_speed := self.mongodb_client.query_playback_speed(self._tts_language_identifier)) is not None:
                return preset_playback_speed
            else:
                return 1.0

    def change_playback_speed(self, playback_speed: float):
        self.mongodb_client.insert_playback_speed(self._tts_language_identifier, playback_speed)

    def download_tts_audio(self, text: str) -> str:
        audio_file_path = f'{self._TTS_AUDIO_FILE_PATH}/{get_timestamp()}.mp3'

        GoogleTTS.get_tts_audio(text, self._tts_language_identifier, audio_file_path)
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
