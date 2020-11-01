from typing import *
from collections import abc, defaultdict, Counter

from lingularity.backend.trainers.components.mappings.token.types import Token
from lingularity.backend.utils import either, iterables, spacy as spacy_utils, strings


ParaphrasesTokens = List[List[Token]]
ParaphrasesTokensList = List[ParaphrasesTokens]


class TokenOccurrencesMap(defaultdict):
    _Type = DefaultDict[str, int]
    _INCLUSION_POS_TYPES = ('VERB', 'NOUN', 'ADJ', 'ADV', 'ADP')

    def __init__(self, language: Optional[str] = None):
        super().__init__(int)

    def create_off_ordinary_tokens(self, paraphrases_tokens_list: List[List[List[str]]]):
        self._display_creation_kick_off_message(token_kind='ordinary')
        for paraphrases_tokens in paraphrases_tokens_list:
            self._insert_paraphrases_tokens(paraphrases_tokens)

    def create_off_spacy_tokens(self, paraphrases_tokens_list: List[List[List[spacy_utils.Token]]]):
        self._display_creation_kick_off_message(token_kind='spacy')

        for paraphrases_tokens in paraphrases_tokens_list:
            filtered_paraphrases_tokens = (filter(lambda token: token.pos_ in self._INCLUSION_POS_TYPES, tokens) for tokens in paraphrases_tokens)
            paraphrases_lemmas = (map(lambda token: token.lemma_, tokens) for tokens in filtered_paraphrases_tokens)
            self._insert_paraphrases_tokens(paraphrases_tokens=paraphrases_lemmas)

    def _display_creation_kick_off_message(self, token_kind: str):
        print(f'Creating {" ".join(strings.split_at_uppercase(self.__class__.__name__))} off {token_kind} tokens...')

    def _insert_paraphrases_tokens(self, paraphrases_tokens: Iterable[Iterable[str]]):
        for token, occurrences in self._inter_paraphrases_duplicate_stripped_tokens(paraphrases_tokens).items():
            self[token] += occurrences

    @staticmethod
    def _inter_paraphrases_duplicate_stripped_tokens(paraphrases_tokens: Iterable[Iterable[str]]) -> Counter:
        token_counter = Counter()
        for tokens in paraphrases_tokens:
            token_counter += Counter(tokens) - token_counter
        return token_counter