from typing import Set
from abc import ABC

from backend import MongoDBClient
from backend import string_resources


class StaticClass(ABC):
    """ Baseclass disallowing instantiation of subclasses """

    def __init_subclass__(cls, **kwargs):
        if StaticClass.__init__ is not cls.__init__:
            raise TypeError


class State(StaticClass):
    """ Global state persisting throughout program runtime, carrying entirety
        of integral user data required by a multitude of components
        and thus allowing for prevention of redundant database queries """

    __slots__ = ()

    username: str
    is_new_user: bool

    non_english_language: str
    train_english: bool

    language: str
    vocabulary_available: bool

    user_languages: Set[str]

    @staticmethod
    def set_user(username: str, is_new_user: bool):
        """ Assumes previous setting of user in database

            Sets:
                username
                user_languages queried from database """

        State.username = username
        State.is_new_user = is_new_user

        State.user_languages = set(MongoDBClient.instance().query_languages())

    @staticmethod
    def set_language(non_english_language: str, train_english: bool):
        """ Assumes previous setting of user in database

            Sets:
                non_english_language
                train_english
                language
                vocabulary_available

            And adds language to user_languages """

        State.non_english_language = non_english_language
        State.train_english = train_english

        State.language = [non_english_language, string_resources.ENGLISH][train_english]
        State.user_languages.add(State.language)

        State.vocabulary_available = State.language in set(MongoDBClient.instance().query_vocabulary_possessing_languages())
