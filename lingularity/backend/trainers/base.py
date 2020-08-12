from typing import List, Optional, Iterator, Any, Sequence, Tuple
import os
from abc import ABC
from functools import cached_property
import time

import nltk
import numpy as np
import gtts
import vlc
from mutagen.mp3 import MP3

from lingularity.backend.database import MongoDBClient
from lingularity.utils.time import get_timestamp


class TrainerBackend(ABC):
    _BASE_LANGUAGE_DATA_PATH = f'{os.getcwd()}/language_data'
    _TTS_AUDIO_FILE_PATH = f'{os.getcwd()}/tts_audio_files'

    _DEFAULT_NAMES = ('Tom', 'Mary')
    _LANGUAGE_2_NAMES = {
        'Italian': ('Alessandro', 'Christina'),
        'French': ('Antoine', 'Amelie'),
        'Spanish': ('Emilio', 'Luciana'),
        'Hungarian': ('László', 'Zsóka'),
        'German': ('Günther', 'Irmgard')
    }

    def __init__(self, non_english_language: str, train_english: bool, mongodb_client: MongoDBClient):
        if not os.path.exists(self._BASE_LANGUAGE_DATA_PATH):
            os.mkdir(self._BASE_LANGUAGE_DATA_PATH)

        self._non_english_language = non_english_language
        self._train_english = train_english
        self.names_convertible: bool = self._LANGUAGE_2_NAMES.get(self._non_english_language) is not None
        self._tts_language_abbreviation: Optional[str] = {v: k for k, v in gtts.lang.tts_langs().items()}.get(self._non_english_language)
        self.tts_available: bool = self._tts_language_abbreviation is not None

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

    @cached_property
    def stemmer(self) -> Optional[nltk.stem.SnowballStemmer]:
        assert self.language is not None, 'Stemmer to be initially called after language setting'

        if (lowered_language := self.language.lower()) in nltk.stem.SnowballStemmer.languages:
            return nltk.stem.SnowballStemmer(lowered_language)
        else:
            return None

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
        sentence_data = self._parse_sentence_data()
        return sentence_data, self._query_lets_go_translation(sentence_data)

    def _parse_sentence_data(self) -> np.ndarray:
        data = open(self.sentence_file_path, 'r', encoding='utf-8').readlines()
        split_data = [i.split('\t') for i in data]

        # remove reference appendices from source file if newly downloaded
        if len(split_data[0]) > 2:
            bilingual_sentence_data = ['\t'.join(row_splits[:2]) + '\n' for row_splits in split_data]
            with open(self.sentence_file_path, 'w', encoding='utf-8') as write_file:
                write_file.writelines(bilingual_sentence_data)
            split_data = [i.split('\t') for i in bilingual_sentence_data]

        for i, row in enumerate(split_data):
            split_data[i][1] = row[1].strip('\n')

        if self._train_english:
            split_data = [list(reversed(row)) for row in split_data]

        return np.asarray(split_data)

    @staticmethod
    def _query_lets_go_translation(unshuffled_sentence_data: np.ndarray) -> Optional[str]:
        for content, i in ((sentence_pair[0], i) for i, sentence_pair in
                                    enumerate(unshuffled_sentence_data[:int(len(unshuffled_sentence_data) * 0.3)])):
            if content == "Let's go!":
                return unshuffled_sentence_data[i][1]
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

    def accommodate_names(self, sentence: str) -> str:
        """ Assertion of self._convertible name being True to be made before invocation """

        sentence_tokens = sentence[:-1].split(' ')
        punctuation = sentence[-1]

        for name_ind, name in enumerate(self._DEFAULT_NAMES):
            try:
                sentence_tokens[sentence_tokens.index(name)] = self._LANGUAGE_2_NAMES[self.language][name_ind]
            except ValueError:
                pass
        return ' '.join(sentence_tokens) + punctuation

    # -----------------
    # .TTS
    # -----------------
    def download_tts_audio(self, text: str) -> str:
        audio_file_path = f'{self._TTS_AUDIO_FILE_PATH}/{get_timestamp()}.mp3'

        gtts.gTTS(text, lang=self._tts_language_abbreviation).save(audio_file_path)
        return audio_file_path

    @staticmethod
    def play_audio_file(audio_file_path: str, suspend_program_for_duration=False):
        vlc.MediaPlayer(audio_file_path).play()

        if suspend_program_for_duration:
            duration = MP3(audio_file_path).info.length - 0.2
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
        assert self.mongodb_client is not None

        update_args = (self.__str__(), n_trained_items)

        self.mongodb_client.update_last_session_statistics(*update_args)
        self.mongodb_client.inject_session_statistics(*update_args)

    def __str__(self):
        return self.__class__.__name__[0].lower()
