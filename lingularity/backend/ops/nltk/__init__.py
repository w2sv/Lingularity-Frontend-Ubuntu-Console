from typing import List, Tuple

from nltk.corpus import wordnet as wn
from nltk.corpus.reader.wordnet import Lemma


WN_NOUN = 'n'
WN_VERB = 'v'
WN_ADJECTIVE = 'a'
WN_ADJECTIVE_SATELLITE = 's'
WN_ADVERB = 'r'


def _pos(lemma: Lemma) -> str:
    """
        Returns:
            part of speech tag of lemma """

    return lemma.synset().name().split('.')[1]


def get_related_lemmas(word: str, pos: str) -> List[Tuple[Lemma, List[Lemma]]]:
    synsets = wn.synsets(word, pos=pos)

    if not synsets:
        return []

    # Get all lemmas of the word (consider 'a'and 's' equivalent)
    lemmas = []
    for s in synsets:
        for l in s.lemmas():
            if _pos(l) == pos or pos in (WN_ADJECTIVE, WN_ADJECTIVE_SATELLITE) and _pos(l) in (
            WN_ADJECTIVE, WN_ADJECTIVE_SATELLITE):
                lemmas += [l]

    # Get related forms
    return [(l, l.derivationally_related_forms()) for l in lemmas]


def get_related_pos(word: str, from_pos: str, to_pos: str) -> List[Tuple[str, float]]:
    """ https://stackoverflow.com/questions/14489309/convert-words-between-verb-noun-adjective-forms
        transform words given from/to POS tags """

    lemmas_with_related_lemmas = get_related_lemmas(word, pos=from_pos)

    # filter only the desired pos (consider 'a' and 's' equivalent)
    related_target_pos_lemmas = []
    for lwrl in lemmas_with_related_lemmas:
        for l in lwrl[1]:
            if _pos(l) == to_pos or to_pos in (WN_ADJECTIVE, WN_ADJECTIVE_SATELLITE) and _pos(l) in (WN_ADJECTIVE, WN_ADJECTIVE_SATELLITE):
                related_target_pos_lemmas += [l]

    # Extract the words from the lemmas
    words = [l.name() for l in related_target_pos_lemmas]
    len_words = len(words)

    # Build the result in the form of a list containing tuples (word, probability)
    result = [(w, float(words.count(w)) / len_words) for w in set(words)]
    result.sort(key=lambda w: -w[1])

    # return all the possibilities sorted by probability
    return result


print(get_related_pos('German', WN_ADJECTIVE, WN_NOUN))