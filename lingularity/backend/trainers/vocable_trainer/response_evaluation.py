from aenum import NoAliasEnum

from lingularity.backend.utils.strings import get_article_stripped_noun


class ResponseEvaluation(NoAliasEnum):
    NoResponse = 0.0
    Wrong = 0.0
    MissingArticle = 0.5
    WrongArticle = 0.5
    AlmostCorrect = 0.5
    AccentError = 0.75
    Correct = 1.0


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
