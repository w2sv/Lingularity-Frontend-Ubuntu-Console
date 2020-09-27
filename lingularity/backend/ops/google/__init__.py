""" google libraries demanding language arguments to be passed in corresponding language,
    as well as in the bulk of cases 2-letter comprising abbreviation,
        e.g. Spanish -> es
             German -> de
             French -> fr """


from abc import ABC
from typing import Optional, Dict


class GoogleOp(ABC):
    def __init__(self, language_2_identifier: Dict[str, str]):
        """ Args:
                language_2_identifier: uppercase language to lowercase identifier,
                                       e.g. {'Afrikaans': 'af', 'Albanian': 'sq', ...} """

        assert next(iter(language_2_identifier.keys())).istitle()

        self._language_2_identifier = language_2_identifier

    def get_identifier(self, query_language: str) -> Optional[str]:
        """ Args:
                query_language: written out language in english as title,
                                e.g. Spanish
            Returns:
                in case of several eligible language variations:
                    first matching google language identifier
                otherwise:
                    the one sole corresponding one """

        if (identifier := self._language_2_identifier.get(query_language)) is not None:
            return identifier
        for _language, identifier in self._language_2_identifier.items():
            if _language.startswith(query_language):
                return identifier
        return None

    def get_dialect_choices(self, query_language: str) -> Optional[Dict[str, str]]:
        """ Returns:
                in case of >= 2 dialects/variations eligible:
                    {query_language_dialect: identifier}: Dict[str, str]

                    e.g. {'French': 'fr', 'French (Canada)': 'fr-ca', 'French (France)': 'fr-fr'} for TTS
                otherwise:
                    None """

        if len((dialect_choices := [language for language in self._language_2_identifier.keys() if language.startswith(query_language)])) > 1:
            dialect_to_identifier = {dialect: self._language_2_identifier[dialect] for dialect in dialect_choices}
            dialect_to_identifier.pop(query_language, None)
            return dialect_to_identifier
        return None
