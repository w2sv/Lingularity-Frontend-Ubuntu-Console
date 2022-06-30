from typing import Set

from backend.src.database import UserMongoDBClient
from backend.src.string_resources import string_resources
from monostate import MonoState


class State(MonoState):
    """ Global state persisting throughout program runtime, carrying entirety
        of integral user data required by a multitude of components
        and thus allowing for prevention of redundant database queries """

    def __init__(self, username: str, is_new_user: bool):
        super().__init__(instance_kwarg_name='state')

        self.username = username
        self.is_new_user = is_new_user

        self.user_languages: Set[str] = set(UserMongoDBClient.instance().query_languages())

        self._language: str = None  # type: ignore
        self.vocabulary_available: bool = None  # type: ignore

        self.non_english_language: str = None  # type: ignore
        self.train_english: bool = None  # type: ignore

    @property
    def language(self) -> str:
        return self._language

    @language.setter
    def language(self, new: str):
        self._language = new
        self.user_languages.add(new)
        self.vocabulary_available = new in set(UserMongoDBClient.instance().query_vocabulary_possessing_languages())

    def set_language(self, non_english_language: str, train_english: bool):
        """ Assumes previous setting of user in database

            Sets:
                non_english_language
                train_english
                language
                vocabulary_available """

        self.non_english_language = non_english_language
        self.train_english = train_english

        self.language = [non_english_language, string_resources['english']][train_english]
