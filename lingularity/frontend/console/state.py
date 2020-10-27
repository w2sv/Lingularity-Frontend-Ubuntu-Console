from lingularity.backend.resources import strings as string_resources


class State:
    username: str
    non_english_language: str
    train_english: bool
    language: str

    @staticmethod
    def set_language(non_english_language: str, train_english: bool):
        State.non_english_language = non_english_language
        State.train_english = train_english
        State.language = [non_english_language, string_resources.ENGLISH][train_english]
