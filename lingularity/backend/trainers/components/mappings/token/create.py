from typing import *
from collections import defaultdict

from tqdm import tqdm

from lingularity.backend.utils import iterables, strings
from lingularity.backend.trainers.components.sentence_data import SentenceData
from lingularity.backend.trainers.components.mappings.token.sentence_indices import get_token_sentence_indices_map, LemmaSentenceIndicesMap
from lingularity.backend.trainers.components.mappings.token.sentence_indices.base import SentenceIndex2UniqueTokens, TokenSentenceIndicesMap
from lingularity.backend.trainers.components.mappings.token.occurrences import TokenOccurrencesMap, ParaphrasesTokensList, ParaphrasesTokens
from lingularity.backend.trainers.components.mappings.token.types import Token


assert __name__ == '__main__', 'module solely to be invoked as main'


EnglishSentence2ParaphrasesWithIndices = DefaultDict[str, List[Tuple[str, int]]]


def create_token_maps(language: str) -> Tuple[TokenSentenceIndicesMap, TokenOccurrencesMap]:
    sentence_data = SentenceData(language=language)

    token_sentence_indices_map = get_token_sentence_indices_map(language=language)
    print(f'{token_sentence_indices_map.__class__.__name__} available')

    # procure token maps foundations
    sentence_index_2_tokens, paraphrases_tokens_list = _token_maps_foundations(sentence_data, tokenize=token_sentence_indices_map.tokenize)

    # create token maps
    token_sentence_indices_map.create(sentence_index_2_tokens)

    token_occurrences_map = TokenOccurrencesMap()
    if type(token_sentence_indices_map) is LemmaSentenceIndicesMap:
        token_occurrences_map.create_off_spacy_tokens(paraphrases_tokens_list)
    else:
        token_occurrences_map.create_off_ordinary_tokens(paraphrases_tokens_list)

    return token_sentence_indices_map, token_occurrences_map

def _token_maps_foundations(
        sentence_data: SentenceData,
        tokenize: Callable[[str], List[Token]]) -> Tuple[SentenceIndex2UniqueTokens, ParaphrasesTokensList]:

    english_sentence_2_paraphrases_with_indices = _english_sentence_paraphrases_with_indices_map(sentence_data=sentence_data[:1_000])

    sentence_index_2_unique_tokens: SentenceIndex2UniqueTokens = {}
    paraphrases_tokens_list: ParaphrasesTokensList = []

    proper_nouns: Set[str] = sentence_data.deduce_proper_nouns()

    print('Creating token maps foundations...')
    for paraphrases_with_indices in tqdm(english_sentence_2_paraphrases_with_indices.values()):
        paraphrases, indices = iterables.unzip(paraphrases_with_indices)

        # preprocess paraphrases
        paraphrases = _preprocess_paraphrases(paraphrases)

        # tokenize paraphrases
        paraphrases_tokens = [tokenize(sentence) for sentence in paraphrases]

        # filter, process tokens
        paraphrases_tokens = _process_paraphrases_tokens(paraphrases_tokens, proper_nouns=proper_nouns)

        sentence_index_2_unique_tokens.update({index: set(comprising_tokens) for index, comprising_tokens in zip(indices, paraphrases_tokens)})
        paraphrases_tokens_list.append(paraphrases_tokens)

    return sentence_index_2_unique_tokens, paraphrases_tokens_list


def _english_sentence_paraphrases_with_indices_map(sentence_data: SentenceData) -> EnglishSentence2ParaphrasesWithIndices:
    english_sentence_2_paraphrases = defaultdict(list)

    print('Creating paraphrases map...')
    for i, (english_sentence, foreign_sentence) in enumerate(tqdm(sentence_data)):
        english_sentence_2_paraphrases[english_sentence].append((foreign_sentence, i))

    return english_sentence_2_paraphrases


def _preprocess_paraphrases(paraphrases: List[str]) -> Iterator[str]:
    """ Removes unicode, as well as special characters """

    unicode_stripped = map(lambda paraphrase: strings._strip_unicode(paraphrase), paraphrases)
    return map(lambda paraphrase: strings.strip_special_characters(paraphrase, include_apostrophe=False, include_dash=False), unicode_stripped)


def _process_paraphrases_tokens(paraphrases_tokens: ParaphrasesTokens, proper_nouns: Set[str]) -> List[List[str]]:
    """ Removes proper nouns, tokens containing digits from paraphrases tokens,
        converts tokens to lowercase """

    for i, paraphrase_tokens in enumerate(paraphrases_tokens):
        lowercase_paraphrase_tokens = (token.lower() for token in paraphrase_tokens)
        paraphrases_tokens[i] = list(filter(lambda token: token not in proper_nouns and strings.is_digit_free(token), lowercase_paraphrase_tokens))

    return paraphrases_tokens


token_sentence_indices_map, token_occurrences_map = create_token_maps(language='Urdu')
# print(token_sentence_indices_map)
print(token_occurrences_map)