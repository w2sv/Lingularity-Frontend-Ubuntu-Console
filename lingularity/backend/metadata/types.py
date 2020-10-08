from typing import List, Optional, Dict, Union, DefaultDict

from mypy_extensions import TypedDict


class ForenameConversionData(TypedDict):
    maleForenames: Dict[str, List[str]]
    femaleForenames: Dict[str, List[str]]
    demonym: Optional[str]


class LanguageMetadataValue(TypedDict):
    sentenceDataDownloadLinks: Dict[str, str]
    countriesEmployedIn: List[str]
    translations: Dict[str, Union[str, List[str]]]


LanguageMetadata = DefaultDict[str, LanguageMetadataValue]
CountryMetadata = Dict[str, Optional[ForenameConversionData]]
