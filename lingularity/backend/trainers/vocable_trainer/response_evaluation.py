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


def get_response_evaluation(response: str, translation: str) -> ResponseEvaluation:
    response = response.strip(' ')

    if not len(response):
        return ResponseEvaluation.NoResponse  # type: ignore

    elif response == translation:
        return ResponseEvaluation.Correct  # type: ignore

    elif response == unidecode(translation):
        return ResponseEvaluation.AccentError  # type: ignore

    elif _n_char_deviations(response, translation) <= _n_tolerable_char_deviations(translation):
        return ResponseEvaluation.AlmostCorrect  # type: ignore

    elif _article_missing(response, translation):
        return ResponseEvaluation.MissingArticle  # type: ignore

    elif _wrong_article(response, translation):
        return ResponseEvaluation.WrongArticle  # type: ignore

    return ResponseEvaluation.Wrong  # type: ignore


def _wrong_article(response: str, translation: str) -> bool:
    contained_nouns = set(map(get_article_stripped_noun, [response, translation]))
    return len(contained_nouns) == 1 and next(iter(contained_nouns)) is not None


def _article_missing(response: str, translation: str) -> bool:
    return get_article_stripped_noun(translation) == response


def _n_tolerable_char_deviations(translation: str) -> int:
    N_ALLOWED_NON_WHITESPACE_CHARS_PER_DEVIATION = 4

    return len(translation.replace(' ', '')) // N_ALLOWED_NON_WHITESPACE_CHARS_PER_DEVIATION


def _n_char_deviations(response, translation) -> int:
    n_deviations = 0

    modified_response = response
    for i in range(len(translation)):
        try:
            if modified_response[i] != translation[i]:
                n_deviations += 1

                if len(modified_response) < len(translation):
                    modified_response = modified_response[:i] + ' ' + modified_response[i:]

                elif len(modified_response) > len(translation):
                    modified_response = modified_response[:i] + modified_response[i + 1:]
        except IndexError:
            n_deviations += len(translation) - len(response)
            break

    return n_deviations


if __name__ == '__main__':
    print(get_response_evaluation(response='baretto', translation='il baretto'))
    print(get_response_evaluation(response='la baretto', translation='il baretto'))