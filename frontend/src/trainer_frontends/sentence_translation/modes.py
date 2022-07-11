from enum import Enum

from backend.src.trainers.sentence_translation import modes
from backend.src.trainers.sentence_translation.modes import SentenceDataFilter
from backend.src.utils.strings.splitting import split_at_uppercase


class SentenceFilterMode(Enum):
    DictionExpansion = 'diction_expansion'
    Simple = 'simple'
    Random = 'random'

    @property
    def display_name(self) -> str:
        return ' '.join(split_at_uppercase(self.name))


MODE_2_EXPLANATION = {
    SentenceFilterMode.DictionExpansion: 'show me sentences containing rather infrequently used vocabulary',
    SentenceFilterMode.Simple: 'show me sentences comprising exclusively commonly used vocabulary',
    SentenceFilterMode.Random: 'just hit me with dem sentences'
}


def get_sentence_filter(mode: SentenceFilterMode) -> SentenceDataFilter:
    return getattr(modes, mode.value).filter_sentence_data