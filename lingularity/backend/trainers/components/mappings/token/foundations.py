from typing import *
from collections import defaultdict

from tqdm import tqdm

from lingularity.backend.utils import iterables, strings
from lingularity.backend.trainers.components.sentence_data import SentenceData
from lingularity.backend.trainers.components.mappings.base import _display_creation_kickoff_message
from lingularity.backend.trainers.components.mappings.token.sentence_indices.base import SentenceIndex2UniqueTokens
from lingularity.backend.trainers.components.mappings.token.occurrences import (
    ParaphrasesTokensList,
    ParaphrasesTokens,
    ParaphrasesPOSTagsList,
)


def token_maps_foundations(
        sentence_data: SentenceData,
        tokenize_with_pos_tags: Callable[[str], List[Tuple[str, str]]]
) -> Tuple[SentenceIndex2UniqueTokens, Tuple[ParaphrasesTokensList, ParaphrasesPOSTagsList]]:

    # create paraphrases map
    english_sentence_2_paraphrases_with_indices = _english_sentence_paraphrases_with_indices_map(sentence_data=sentence_data)

    # define foundations
    sentence_index_2_unique_tokens: SentenceIndex2UniqueTokens = {}
    paraphrases_tokens_list: ParaphrasesTokensList = []
    paraphrases_pos_tags_list: ParaphrasesPOSTagsList = []

    # procure proper nouns
    proper_nouns: Set[str] = sentence_data.deduce_proper_nouns()

    print('Creating token maps foundations...')
    for paraphrases_with_indices in tqdm(english_sentence_2_paraphrases_with_indices.values()):
        paraphrases, indices = iterables.unzip(paraphrases_with_indices)

        # tokenize paraphrases and procure pos tags
        paraphrases_tokens_with_pos_tags: List[List[Tuple[str, str]]] = [tokenize_with_pos_tags(sentence) for sentence in paraphrases]
        if any(map(len, paraphrases_tokens_with_pos_tags)):
            paraphrases_tokens, paraphrases_pos_tags = map(iterables.none_stripped, iterables.unzip_longest(map(lambda paraphrase_tokens_with_pos_tags: iterables.unzip(paraphrase_tokens_with_pos_tags), paraphrases_tokens_with_pos_tags)))

            # strip proper nouns, tokens containing digits; convert to lowercase
            paraphrases_tokens = _process_paraphrases_tokens(paraphrases_tokens, proper_nouns=proper_nouns)

            # update foundations
            sentence_index_2_unique_tokens.update({index: set(comprising_tokens) for index, comprising_tokens in zip(indices, paraphrases_tokens)})
            paraphrases_tokens_list.append(paraphrases_tokens)
            paraphrases_pos_tags_list.append(paraphrases_pos_tags)

    return sentence_index_2_unique_tokens, (paraphrases_tokens_list, paraphrases_pos_tags_list)


@_display_creation_kickoff_message('Creating paraphrases map...')
def _english_sentence_paraphrases_with_indices_map(sentence_data: SentenceData) -> DefaultDict[str, List[Tuple[str, int]]]:
    english_sentence_2_paraphrases = defaultdict(list)

    for i, (english_sentence, foreign_sentence) in enumerate(tqdm(sentence_data)):
        english_sentence_2_paraphrases[english_sentence].append((foreign_sentence, i))

    return english_sentence_2_paraphrases


def _process_paraphrases_tokens(paraphrases_tokens: ParaphrasesTokens, proper_nouns: Set[str]) -> ParaphrasesTokens:
    """ Removes proper nouns, tokens containing digits from paraphrases tokens,
        converts tokens to lowercase """

    for i, paraphrase_tokens in enumerate(paraphrases_tokens):
        lowercase_paraphrase_tokens = (token.lower() for token in paraphrase_tokens)
        paraphrases_tokens[i] = list(filter(lambda token: token not in proper_nouns and strings.is_digit_free(token), lowercase_paraphrase_tokens))

    return paraphrases_tokens
