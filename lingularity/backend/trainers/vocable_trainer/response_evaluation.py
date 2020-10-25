from typing import Tuple

from aenum import NoAliasEnum
from unidecode import unidecode

from lingularity.backend.utils.strings import get_article_stripped_noun


class ResponseEvaluation(NoAliasEnum):
    NoResponse = 0.0
    Wrong = 0.0
    MissingArticle = 0.5
    WrongArticle = 0.5
    AlmostCorrect = 0.5
    AccentError = 0.75
    Correct = 1.0


def get_response_evaluation(response: str, ground_truth: str, vocable_identification_aid='') -> Tuple[str, ResponseEvaluation]:
    response, evaluation = response.strip(' '), None

    if not len(response):
        evaluation = ResponseEvaluation.NoResponse
    else:
        response = vocable_identification_aid + response

        if response == ground_truth:
            evaluation = ResponseEvaluation.Correct

        elif unidecode(response) == unidecode(ground_truth):
            evaluation = ResponseEvaluation.AccentError

        elif _article_missing(response, ground_truth):
            evaluation = ResponseEvaluation.MissingArticle

        elif _wrong_article(response, ground_truth):
            evaluation = ResponseEvaluation.WrongArticle

        elif _almost_correct(response, ground_truth):
            evaluation = ResponseEvaluation.AlmostCorrect

        else:
            evaluation = ResponseEvaluation.Wrong

    return response, evaluation  # type: ignore


# ---------------
# Article related
# ---------------
def _wrong_article(response: str, ground_truth: str) -> bool:
    contained_nouns = list(map(get_article_stripped_noun, [response, ground_truth]))
    return len(set(contained_nouns)) == 1 and contained_nouns[0] is not None


def _article_missing(response: str, ground_truth: str) -> bool:
    return get_article_stripped_noun(ground_truth) == response


# ---------------
# Almost Correct
# ---------------
def _almost_correct(response: str, ground_truth: str) -> bool:
    TOLERATED_CHAR_DEVIATIONS_PER_TOKEN = 1

    response_tokens = response.split(' ')
    ground_truth_tokens = ground_truth.split(' ')

    if len(response_tokens) != len(ground_truth_tokens):
        return False

    for response_token, ground_truth_token, in zip(response_tokens, ground_truth_tokens):
        n_char_deviations = _n_char_deviations(response_token, ground_truth_token)
        if n_char_deviations > TOLERATED_CHAR_DEVIATIONS_PER_TOKEN or n_char_deviations == TOLERATED_CHAR_DEVIATIONS_PER_TOKEN and not _char_deviation_tolerated(ground_truth_token):
            return False
    return True


def _char_deviation_tolerated(ground_truth: str) -> bool:
    return len(ground_truth) >= 4


def _n_char_deviations(response: str, ground_truth: str) -> int:
    n_deviations = 0

    adjusted_response = response
    for i in range(len(ground_truth)):

        # exit if i has exceeded length of adjusted response
        if i == len(adjusted_response):
            n_deviations += len(ground_truth) - len(response)
            break

        elif adjusted_response[i] != ground_truth[i]:
            n_deviations += 1

            # enable covering of cases in which one character has been omitted,
            # such as in sopare <-> scopare
            if len(ground_truth) > len(adjusted_response) and adjusted_response[i] == ground_truth[i+1]:
                adjusted_response = adjusted_response[:i] + ' ' + adjusted_response[i:]

            # enable covering of cases in which character has been incorrectly inserted,
            # such as in scopaare <-> scopare
            elif len(adjusted_response) > len(ground_truth) and adjusted_response[i+1] == ground_truth[i]:
                adjusted_response = adjusted_response[:i] + adjusted_response[i + 1:]
                i -= 1

    return n_deviations
