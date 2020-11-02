from typing import *
import collections

from tqdm import tqdm

from lingularity.backend.utils import strings
from lingularity.backend.trainers.components.mappings.base import CustomMapping


ParaphrasesTokens = List[List[str]]
ParaphrasesTokensList = List[ParaphrasesTokens]

ParaphrasesPOSTagsList = ParaphrasesTokensList


class TokenOccurrencesMap(collections.defaultdict, CustomMapping):
    _Type = DefaultDict[str, int]
    _INCLUSION_POS_TYPES = {'VERB', 'NOUN', 'ADJ', 'ADV', 'ADP', 'INTJ'}

    def __init__(self, language: Optional[str] = None):
        super().__init__(int)

    def create(
            self,
            paraphrases_tokens_list: ParaphrasesTokensList,
            paraphrases_pos_tags_list: Optional[ParaphrasesPOSTagsList]
    ):
        if paraphrases_pos_tags_list is not None:
            self._create_with_pos_tags(paraphrases_tokens_list, paraphrases_pos_tags_list)
        else:
            self._create_without_pos_tags(paraphrases_tokens_list)

    def _create_without_pos_tags(self, paraphrases_tokens_list: ParaphrasesTokensList):
        self._display_creation_kick_off_message(pos_tag_creation=False)

        for paraphrases_tokens in tqdm(paraphrases_tokens_list):
            self._insert_paraphrases_tokens(paraphrases_tokens)

    def _create_with_pos_tags(
            self,
            paraphrases_tokens_list: ParaphrasesTokensList,
            paraphrases_pos_tags_list: ParaphrasesPOSTagsList
    ):
        self._display_creation_kick_off_message(pos_tag_creation=True)

        for paraphrases_tokens, paraphrases_pos_tags in tqdm(zip(paraphrases_tokens_list, paraphrases_pos_tags_list), total=len(paraphrases_tokens_list)):
            filtered_paraphrases_tokens = ((token for token, pos_tag in zip(paraphrase_tokens, paraphrase_pos_tags) if pos_tag in self._INCLUSION_POS_TYPES) for paraphrase_tokens, paraphrase_pos_tags in zip(paraphrases_tokens, paraphrases_pos_tags))
            self._insert_paraphrases_tokens(paraphrases_tokens=filtered_paraphrases_tokens)

    @staticmethod
    def _display_creation_kick_off_message(pos_tag_creation: bool):
        print(f'Creating {" ".join(strings.split_at_uppercase(TokenOccurrencesMap.__name__))} with{["out", ""][pos_tag_creation]} POS tags...')

    def _insert_paraphrases_tokens(self, paraphrases_tokens: Iterable[Iterable[str]]):
        for token, occurrences in self._inter_paraphrases_duplicate_stripped_tokens(paraphrases_tokens).items():
            self[token] += occurrences

    @staticmethod
    def _inter_paraphrases_duplicate_stripped_tokens(paraphrases_tokens: Iterable[Iterable[str]]) -> Counter[str]:
        token_counter: Counter[str] = collections.Counter()
        for tokens in paraphrases_tokens:
            token_counter += collections.Counter(tokens) - token_counter
        return token_counter


def create_token_occurrences_map(
        paraphrases_tokens_list: ParaphrasesTokensList,
        paraphrases_pos_tags_list: Optional[ParaphrasesPOSTagsList]
) -> TokenOccurrencesMap:

    token_occurrences_map = TokenOccurrencesMap()
    token_occurrences_map.create(paraphrases_tokens_list=paraphrases_tokens_list,
                                 paraphrases_pos_tags_list=paraphrases_pos_tags_list)
    return token_occurrences_map
