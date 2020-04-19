from typing import Optional
import os
import platform
from subprocess import Popen
import json

from .sentence_translation import SentenceTranslationTrainer
from .vocabulary_training import VocabularyTrainer
from .trainer import Trainer
from .utils.datetime import parse_date, today_or_yesterday


_TRAINERS = {'sentence translation': SentenceTranslationTrainer, 'vocabulary trainer': VocabularyTrainer}


def initialize_terminal():
    if platform.system() == 'Windows':
        Popen(f'{os.getcwd()}/terminal_inits/windows.cmd', cwd=os.getcwd())
    Trainer.clear_screen()


def last_session_display():
    # TODO: write last training session to training history to prevent date parity based mix-ups
    latest_training_session, corresponding_language, corresponding_entry = [None] * 3
    if not os.path.exists(Trainer.BASE_DATA_PATH):
        return

    for language in os.listdir(Trainer.BASE_DATA_PATH):
        language_training_documentation_file = f'{Trainer.BASE_DATA_PATH}/{language}/training_documentation.json'
        if not os.path.exists(language_training_documentation_file):
            continue
        documentation = json.load(open(language_training_documentation_file, 'r'))
        date_max = max(documentation.keys())
        if not latest_training_session or date_max > latest_training_session:
            latest_training_session, corresponding_language, corresponding_entry = date_max, language, documentation[date_max]
    if latest_training_session is not None:
        print(f'\t\t\tLast session: faced ', end='')
        if corresponding_entry.get('v') is not None:
            print(f"{corresponding_entry['v']} {corresponding_language} vocables ", end='')
        if len(corresponding_entry) == 2:
            print('and ', end='')
        if corresponding_entry.get('s') is not None:
            print(f"{corresponding_entry['s']} {corresponding_language} sentences ", end='')
        parsed_date = parse_date(latest_training_session)
        toy = today_or_yesterday(parsed_date)
        if toy is not None:
            print(toy, '\n')
        else:
            print(f'the {parsed_date.day}th of {parsed_date.strftime("%B")} {parsed_date.year}', '\n')


def display_starting_screen():
    Trainer.clear_screen()
    banner = open(os.path.join(os.getcwd(), 'resources/banner.txt'), 'r').read()
    print(banner)
    print("							W2SV", '\n' * 1)
    print("					         by Janek Zangenberg ", '\n' * 2)
    print("         Sentence data stemming from the Tatoeba Project to be found at http://www.manythings.org/anki", '\n' * 2)
    print('Note: all requested inputs may be merely entered up to a point which allows for an unambigious identification of the intended choice,')
    print("  e.g. 'it' suffices for selecting Italian since there's no other eligible language starting on 'it'", '\n')
    last_session_display()


def add_vocabulary():
    Trainer.clear_screen()
    languages = [language.lower() for language in os.listdir(Trainer.BASE_DATA_PATH)]
    print('EXTENSIBLE VOCABULARY FILES: ')
    [print(language) for language in languages]
    selection = Trainer.resolve_input(input('\nSelect language: ').lower(), languages)
    if selection is None:
        Trainer.recurse_on_invalid_input(add_vocabulary)
    else:
        sentence_trainer = SentenceTranslationTrainer()
        sentence_trainer.language = selection
        while True:
            sentence_trainer.append_2_vocabulary_file()
            try:
                procedure_resolution = Trainer.resolve_input(input("Press Enter to continue adding, otherwise enter 'exit'\t"), ['exit', 'ZUNGENUNMUTSERLABUNG'])
                if procedure_resolution == 'exit':
                    return complete_initialization()
                Trainer.erase_previous_line()
            except SyntaxError:
                pass


def select_training() -> Optional[str]:
    indentation = '\t' * 2
    print("\nSelect Training: ", end='')
    training = Trainer.resolve_input(input(f"{indentation}(S)entence translation{indentation}(V)ocabulary training{indentation}or (a)dd vocabulary\n").lower(), list(_TRAINERS.keys()) + ['add vocabulary'])
    if training is None:
        return Trainer.recurse_on_invalid_input(select_training)
    elif training == 'add vocabulary':
        return add_vocabulary()

    Trainer.clear_screen()
    return training


def commence_training(training_selection: str):
    trainer_instance = _TRAINERS[training_selection]()
    trainer_instance.run()


def complete_initialization():
    initialize_terminal()
    display_starting_screen()
    training_selection = select_training()
    commence_training(training_selection)


if __name__ == '__main__':
    complete_initialization()
