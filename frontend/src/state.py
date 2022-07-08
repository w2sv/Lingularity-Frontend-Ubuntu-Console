from backend.src.database.user_database import UserDatabase
from backend.src.string_resources import string_resources
from monostate import MonoState


class State(MonoState):
    """ Global state persisting throughout program runtime, carrying entirety
        of integral user data required by a multitude of components
        and thus allowing for prevention of redundant database queries """

    @UserDatabase.receiver
    def __init__(self, username: str, is_new_user: bool, user_database: UserDatabase):
        super().__init__()

        self.username = username
        self.is_new_user = is_new_user

        self.user_languages: set[str] = user_database.training_chronic_collection.comprised_languages()

        self._language: str = None  # type: ignore

        self.non_english_language: str = None  # type: ignore
        self.train_english: bool = None  # type: ignore

    @property
    def language(self) -> str:
        return self._language

    @language.setter
    def language(self, new: str):
        self._language = new
        self.user_languages.add(new)

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
