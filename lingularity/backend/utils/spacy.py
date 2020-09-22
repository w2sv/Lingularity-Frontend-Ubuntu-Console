from lingularity.backend.utils.enum import ExtendedEnum


LANGUAGE_2_CODE = {'chinese': 'zh', 'danish': 'da', 'dutch': 'nl', 'english': 'en',
                   'french': 'fr', 'german': 'de', 'greek': 'el', 'italian': 'it',
                   'japanese': 'ja', 'lithuanian': 'lt', 'norwegian': 'nb', 'polish': 'pl',
                   'portuguese': 'pt', 'romanian': 'ro', 'spanish': 'es'}


class POS(ExtendedEnum):
    ProperNoun = 'PROPN'
    Auxiliary = 'AUX'
    Verb = 'VERB'
    Preposition = 'ADP'
    Noun = 'NOUN'
    Symbol = 'SYM'
    Number = 'NUM'
    Pronoun = 'PRON'
    Adjective = 'ADJ'
    Punctuation = 'PUNCT'
