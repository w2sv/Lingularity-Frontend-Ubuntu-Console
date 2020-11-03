from typing import Callable

from lingularity.backend.trainers.components import SentenceData
from lingularity.backend.utils.module_abstraction import abstractmodulemethod
from . import random, simple, diction_expansion


@abstractmodulemethod
def filter_sentence_data():
    pass


SentenceDataFilter = Callable[[SentenceData, str], SentenceData]


if __name__ == '__main__':

    language = 'Italian'

    sentence_data = SentenceData(language, train_english=False)
    print(f'# sentences: {len(sentence_data)}')

    filtered_sentence_data = simple.filter_sentence_data(sentence_data, language)

    print(f'# filtered sentences simple: {len(filtered_sentence_data)}')
    # print(filtered_sentence_data[-30:])
