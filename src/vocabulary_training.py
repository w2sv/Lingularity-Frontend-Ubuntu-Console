from typing import List, Dict, Optional
import os
import json

from .trainer import Trainer


# TODO: test loading, actual training, score alteration ...


class VocabularyTrainer(Trainer):
    def __init__(self):
        super().__init__()

        self.token_2_rowinds: Optional[Dict[str, List[int]]] = None

    @property
    def vocabulary_scores_file_path(self):
        return f'{self.base_data_path}/{self.language}/vocabulary_scores.json'

    def select_language(self) -> str:
        eligible_languages = [language for language in os.listdir(self.base_data_path) if 'vocabulary.txt' in os.listdir(f'{self.base_data_path}/{language}')]
        print('ELIGIBLE LANGUAGES: ')
        [print(language) for language in sorted(eligible_languages)]
        language_selection = input('\nEnter desired language:\n').title()
        if language_selection not in eligible_languages:
            return self.recurse_on_invalid_input(self.select_language)
        return language_selection

    def procure_word_2_rowinds_map(self):
        sentence_data = self.parse_sentence_data()
        token_2_rowinds = {}
        for i, sentence in sentence_data[:, 1]:
            for token in sentence.split(' '):
                if token_2_rowinds.get(token) is None:
                    token_2_rowinds[token] = [i]
                else:
                    token_2_rowinds[token].append(i)
        return token_2_rowinds

    def parse_vocabulary_scores(self) -> Dict[str, int]:
        with open(self.vocabulary_scores_file_path) as read_file:
            return json.load(read_file)

    def run(self):
        self._language = self.select_language()
        self.token_2_rowinds = self.procure_word_2_rowinds_map()


if __name__ == '__main__':
    VocabularyTrainer().run()

