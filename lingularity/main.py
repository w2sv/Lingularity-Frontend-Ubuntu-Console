from typing import Optional
import os
import platform
from subprocess import Popen
import json

from lingularity.trainers.sentence_translation import SentenceTranslationTrainer
from lingularity.trainers.vocabulary_training import VocabularyTrainer
from lingularity.trainers import Trainer
from lingularity.utils import datetime
from lingularity.utils.input_resolution import recurse_on_invalid_input, resolve_input
from lingularity.utils.output_manipulation import clear_screen, erase_previous_line


TRAINERS = {
    'sentence translation': SentenceTranslationTrainer,
    'vocabulary trainer': VocabularyTrainer
}


def initialize_terminal():
    if platform.system() == 'Windows':
        Popen(f'{os.getcwd()}/shell/windows.cmd', cwd=os.getcwd())
    clear_screen()


def last_session_display():
    # TODO: write last training session to training history to prevent date parity based mix-ups
    latest_training_session, corresponding_language, corresponding_entry = [None] * 3
    if not os.path.exists(Trainer.BASE_LANGUAGE_DATA_PATH):
        return

    for language in os.listdir(Trainer.BASE_LANGUAGE_DATA_PATH):
        language_training_documentation_file = f'{Trainer.BASE_LANGUAGE_DATA_PATH}/{language}/training_documentation.json'
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
        parsed_date = datetime.parse_date_from_string(latest_training_session)
        toy = datetime.today_or_yesterday(parsed_date)
        if toy is not None:
            print(toy, '\n')
        else:
            print(f'the {parsed_date.day}th of {parsed_date.strftime("%B")} {parsed_date.year}', '\n')


def display_starting_screen():
    clear_screen()
    banner = open(os.path.join(os.getcwd(), 'resources/banner.txt'), 'r').read()
    print(banner)
    print("							W2SV", '\n' * 1)
    print("					         by Janek Zangenberg ", '\n' * 2)
    print("         Sentence data stemming from the Tatoeba Project to be found at http://www.manythings.org/anki", '\n' * 2)
    print("Note: all requested inputs may be merely entered up to a point which allows for an unambigious identification of the intended choice,")
    print("  e.g. 'it' suffices for selecting Italian since there's no other eligible language starting on 'it'", '\n')


def add_vocabulary():
    clear_screen()
    languages = [language.lower() for language in os.listdir(Trainer.BASE_LANGUAGE_DATA_PATH)]
    print('EXTENSIBLE VOCABULARY FILES: ')
    [print(language) for language in languages]
    selection = resolve_input(input('\nSelect language: ').lower(), languages)
    if selection is None:
        recurse_on_invalid_input(add_vocabulary)
    else:
        sentence_trainer = SentenceTranslationTrainer()
        sentence_trainer._non_english_language = selection
        while True:
            sentence_trainer._append_2_vocabulary_file()
            try:
                procedure_resolution = resolve_input(input("Press Enter to continue adding, otherwise enter 'exit'\t"), ['exit', 'ZUNGENUNMUTSERLABUNG'])
                if procedure_resolution == 'exit':
                    return complete_initialization()
                erase_previous_line()
            except SyntaxError:
                pass


def select_training() -> Optional[str]:
    indentation = '\t' * 2
    print("\nSelect Training: ", end='')
    training = resolve_input(input(f"{indentation}(S)entence translation{indentation}(V)ocabulary training{indentation}or (a)dd _vocabulary\n").lower(), list(TRAINERS.keys()) + ['add _vocabulary'])
    if training is None:
        return recurse_on_invalid_input(select_training)
    elif training == 'add _vocabulary':
        return add_vocabulary()

    clear_screen()
    return training


def complete_initialization():
    initialize_terminal()
    display_starting_screen()
    last_session_display()
    TRAINERS[select_training()]().run()


if __name__ == '__main__':
    complete_initialization()
