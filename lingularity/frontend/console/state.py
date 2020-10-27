from typing import Set

from lingularity.backend.database import MongoDBClient
from lingularity.backend.resources import strings as string_resources


class State:
    username: str
    non_english_language: str
    train_english: bool
    language: str
    user_languages: Set[str]

    @staticmethod
    def set_user(username: str):
        State.username = username
        State.user_languages = set(MongoDBClient.get_instance().query_languages())

    @staticmethod
    def set_language(non_english_language: str, train_english: bool):
        State.non_english_language = non_english_language
        State.train_english = train_english
        State.language = [non_english_language, string_resources.ENGLISH][train_english]
        State.user_languages.add(State.language)
