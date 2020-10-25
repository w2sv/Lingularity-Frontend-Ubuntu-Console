""" google libraries demanding language arguments to be passed in corresponding language,
    as well as in the bulk of cases 2-letter comprising abbreviation,
        e.g. Spanish -> es
             German -> de
             French -> fr """

from typing import Optional, Dict, List
from abc import ABC


class GoogleOp(ABC):
    _language_2_identifier: Dict[str, str]

    def __init__(self, language_2_identifier: Dict[str, str]):
        """ Args:
                language_2_identifier: uppercase language to lowercase identifier,
                    e.g. {'Afrikaans': 'af', 'Albanian': 'sq', ...} """

        if not hasattr(self.__class__, '_language_2_identifier'):
            self.__class__._language_2_identifier = language_2_identifier

        self._cached_language_repr_2_identifier: Dict[str, str] = {}

    def available_for(self, language: str) -> bool:
        return self._get_identifier(language) is not None

    def _get_identifier(self, query_language: str) -> Optional[str]:
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

        elif (cached_identifier := self._cached_language_repr_2_identifier.get(query_language)) is not None:
            return cached_identifier

        for _language, identifier in self._language_2_identifier.items():
            if _language.startswith(query_language):
                self._cached_language_repr_2_identifier[query_language] = identifier
                return identifier
        return None

    def get_variety_choices(self, query_language: str) -> Optional[List[str]]:
        """ Returns:
                in case of >= 2 dialects/variations eligible:
                    {query_language_dialect: identifier}: Dict[str, str]

                    e.g. {'French': 'fr', 'French (Canada)': 'fr-ca', 'French (France)': 'fr-fr'} for TextToSpeech
                otherwise:
                    None """

        if len((dialect_choices := [language for language in self._language_2_identifier.keys() if query_language != language and language.startswith(query_language)])) > 1:
            return dialect_choices
        return None
