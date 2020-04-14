import os
import time

from .sentence_translation import SentenceTranslationTrainer
from .vocabulary_training import VocabularyTrainer
from .trainer import Trainer

_TRAINERS = {'s': SentenceTranslationTrainer, 'v': VocabularyTrainer}


def display_starting_screen():
    Trainer.clear_screen()
    banner = open(os.path.join(os.getcwd(), 'resources/banner.txt'), 'r').read()
    print(banner)
    print("							W2SV", '\n' * 1)
    print("					         by Janek Zangenberg ", '\n' * 2)
    print("         Sentence data stemming from the Tatoeba Project to be found at http://www.manythings.org/anki", '\n' * 2)
    print('Note: all requested inputs may be merely entered up to a point which allows for an unambigious identification of the intended choice,')
    print("  e.g. 'it' suffices for selecting Italian since there's no other eligible language starting on it", '\n')


def select_training() -> str:
    indentation = '\t' * 4
    print("Select Training: ", end='')
    training = input(f"{indentation}(S)entence translation{indentation}(V)ocabulary training\n").lower()

    if training not in _TRAINERS.keys():
        Trainer.recurse_on_invalid_input(select_training)
        return select_training()

    Trainer.clear_screen()
    return training


def commence_training(training_selection: str):
    trainer_instance = _TRAINERS[training_selection]()
    trainer_instance.run()


if __name__ == '__main__':
    display_starting_screen()
    training_selection = select_training()
    commence_training(training_selection)
