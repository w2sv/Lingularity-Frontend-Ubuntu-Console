from typing import List, Optional, Dict, DefaultDict

from mypy_extensions import TypedDict


class _GenderForenames(TypedDict):
    latinSpelling: List[str]
    nativeSpelling: Optional[List[str]]


class ReplacementForenames(TypedDict):
    maleForenames: _GenderForenames
    femaleForenames: _GenderForenames
    demonym: Optional[str]


DefaultForenamesTranslations = Optional[Dict[str, List[str]]]


class _Translations(TypedDict):
    letsGo: Optional[str]
    constitutionQuery: Optional[List[str]]
    defaultForenames: DefaultForenamesTranslations


class _LanguageMetadataValue(TypedDict):
    sentenceDataDownloadLinks: Dict[str, str]
    properties: Dict[str, str]
    countriesEmployedIn: List[str]
    translations: Dict[str, _Translations]


LanguageMetadata = DefaultDict[str, _LanguageMetadataValue]
CountryMetadata = Dict[str, Optional[ReplacementForenames]]
