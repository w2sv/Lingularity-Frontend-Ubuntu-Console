from typing import *
from collections import defaultdict
from itertools import zip_longest

from tqdm import tqdm

from lingularity.backend.utils import iterables, strings
from lingularity.backend.trainers.components.sentence_data import SentenceData
from lingularity.backend.trainers.components.mappings.token.sentence_indices import get_token_sentence_indices_map, LemmaSentenceIndicesMap
from lingularity.backend.trainers.components.mappings.token.sentence_indices.base import SentenceIndex2UniqueTokens, TokenSentenceIndicesMap
from lingularity.backend.trainers.components.mappings.token.occurrences import TokenOccurrencesMap, ParaphrasesTokensList, ParaphrasesTokens, ParaphrasesPOSTagsList


assert __name__ == '__main__', 'module solely to be invoked as main'


EnglishSentence2ParaphrasesWithIndices = DefaultDict[str, List[Tuple[str, int]]]


def create_token_maps(language: str) -> Tuple[TokenSentenceIndicesMap, TokenOccurrencesMap]:
    sentence_data = SentenceData(language=language)

    token_sentence_indices_map = get_token_sentence_indices_map(language=language)
    print(f'{token_sentence_indices_map.__class__.__name__} available')

    # procure token maps foundations
    sentence_index_2_tokens, paraphrases_tokens_list, paraphrases_pos_tags_list = _token_maps_foundations(
        sentence_data=sentence_data,
        tokenize_with_pos_tags=token_sentence_indices_map.tokenize_with_pos_tags
    )

    # create token maps
    token_sentence_indices_map.create(sentence_index_2_tokens)
    token_occurrences_map = TokenOccurrencesMap().create(paraphrases_tokens_list, [None, paraphrases_pos_tags_list][type(token_sentence_indices_map) is LemmaSentenceIndicesMap])

    return token_sentence_indices_map, token_occurrences_map


def _token_maps_foundations(
        sentence_data: SentenceData,
        tokenize_with_pos_tags: Callable[[str], List[Tuple[str, str]]]
) -> Tuple[SentenceIndex2UniqueTokens, ParaphrasesTokensList, ParaphrasesPOSTagsList]:

    english_sentence_2_paraphrases_with_indices = _english_sentence_paraphrases_with_indices_map(sentence_data=sentence_data[1:100])

    sentence_index_2_unique_tokens: SentenceIndex2UniqueTokens = {}
    paraphrases_tokens_list: ParaphrasesTokensList = []
    paraphrases_pos_tags_list: ParaphrasesPOSTagsList = []

    proper_nouns: Set[str] = sentence_data.deduce_proper_nouns()

    print('Creating token maps foundations...')
    for paraphrases_with_indices in tqdm(english_sentence_2_paraphrases_with_indices.values()):
        paraphrases, indices = iterables.unzip(paraphrases_with_indices)

        # tokenize paraphrases
        paraphrases_tokens_with_pos_tags: List[List[Tuple[str, str]]] = [tokenize_with_pos_tags(sentence) for sentence in paraphrases]
        if any(map(len, paraphrases_tokens_with_pos_tags)):
            paraphrases_tokens, paraphrases_pos_tags = map(iterables.none_stripped, zip_longest(*map(lambda paraphrase_tokens_with_pos_tags: zip(*paraphrase_tokens_with_pos_tags), paraphrases_tokens_with_pos_tags)))

            paraphrases_tokens = _process_paraphrases_tokens(paraphrases_tokens, proper_nouns=proper_nouns)

            sentence_index_2_unique_tokens.update({index: set(comprising_tokens) for index, comprising_tokens in zip(indices, paraphrases_tokens)})
            paraphrases_tokens_list.append(paraphrases_tokens)
            paraphrases_pos_tags_list.append(paraphrases_pos_tags)

    return sentence_index_2_unique_tokens, paraphrases_tokens_list, paraphrases_pos_tags_list


def _english_sentence_paraphrases_with_indices_map(sentence_data: SentenceData) -> EnglishSentence2ParaphrasesWithIndices:
    english_sentence_2_paraphrases = defaultdict(list)

    print('Creating paraphrases map...')
    for i, (english_sentence, foreign_sentence) in enumerate(tqdm(sentence_data)):
        english_sentence_2_paraphrases[english_sentence].append((foreign_sentence, i))

    return english_sentence_2_paraphrases


def _process_paraphrases_tokens(paraphrases_tokens: ParaphrasesTokens, proper_nouns: Set[str]) -> List[List[str]]:
    """ Removes proper nouns, tokens containing digits from paraphrases tokens,
        converts tokens to lowercase """

    for i, paraphrase_tokens in enumerate(paraphrases_tokens):
        lowercase_paraphrase_tokens = (token.lower() for token in paraphrase_tokens)
        paraphrases_tokens[i] = list(filter(lambda token: token not in proper_nouns and strings.is_digit_free(token), lowercase_paraphrase_tokens))

    return paraphrases_tokens


token_sentence_indices_map, token_occurrences_map = create_token_maps(language='Burmese')
print(token_sentence_indices_map)
print(token_occurrences_map)