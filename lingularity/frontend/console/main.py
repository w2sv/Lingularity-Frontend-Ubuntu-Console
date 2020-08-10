from typing import Optional
import os
import time
from getpass import getpass

from lingularity.frontend.console.trainers import SentenceTranslationTrainerConsoleFrontend, VocableTrainerConsoleFrontend
from lingularity.database import MongoDBClient
from lingularity.utils.input_resolution import recurse_on_invalid_input, resolve_input
from lingularity.utils.output_manipulation import clear_screen, erase_lines
from lingularity.utils.datetime import is_today_or_yesterday, parse_date_from_string


TRAINERS = {
    'sentence translation': SentenceTranslationTrainerConsoleFrontend,
    'vocabulary trainer': VocableTrainerConsoleFrontend
}


def display_starting_screen():
    clear_screen()
    banner = open(f'{os.path.dirname(os.path.abspath(__file__))}/resources/banner.txt', 'r').read()
    print(banner)
    print("							W2SV", '\n' * 1)
    print("					         by Janek Zangenberg ", '\n' * 2)


def login() -> MongoDBClient:
    """ Returns:
            user instantiated client """

    indentation = '				         '
    username = input(f'{indentation}Enter user name: ')
    client = MongoDBClient(username, None)
    if username in client.usernames:
        password, password_input = client.query_password(), getpass(f'{indentation}Enter password: ')
        while password != password_input:
            erase_lines(1)
            password_input = getpass(f'{indentation}Incorrect, try again: ')
        erase_lines(2)

    else:
        mail_address = input('Enter Emailaddress: ')
        password = getpass(f'{indentation}Create password: ')
        client.initialize_user(mail_address, password)
        erase_lines(3)

    return client


def extended_starting_screen(username: str):
    print("         Sentence data stemming from the Tatoeba Project to be found at http://www.manythings.org/anki", '\n' * 2)
    print("Note: all requested inputs may be merely entered up to a point which allows for an unambigious identification of the intended choice,")
    print("  e.g. 'it' suffices for selecting Italian since there's no other eligible language starting on 'it'", '\n' * 2)
    print('\t' * 6, f"What's up {username}?")


def display_last_session_statistics(client: MongoDBClient):
    last_session_metrics = client.query_last_session_statistics()
    last_session_items = 'vocables' if last_session_metrics['trainer'] == 'v' else 'sentences'

    if (today_or_yesterday := is_today_or_yesterday(parse_date_from_string(last_session_metrics['date']))) is not None:
        date_repr = today_or_yesterday
    else:
        parsed_date = parse_date_from_string(last_session_metrics['date'])
        date_repr = f'the {parsed_date.day}th of {parsed_date.strftime("%B")} {parsed_date.year}'

    print('\t'*3, f"You {'already' if date_repr == 'today' else ''} faced {last_session_metrics['faced_items']} {last_session_metrics['language']} {last_session_items} during your last session {date_repr}{'!' if date_repr == 'today' else ''}\n")


def select_training() -> Optional[str]:
    indentation = '\t' * 2
    print("\nWhat would you like to do?: ", end='')
    training = resolve_input(input(f"{indentation}Translate (S)entences{indentation}Train (V)ocabulary{indentation}or (A)dd Vocabulary\n").lower(), list(TRAINERS.keys()) + ['add vocabulary'])
    if training is None:
        print("Couldn't resolve input")
        time.sleep(1)
        erase_lines(4)
        return select_training()
    """elif training == 'add vocabulary':
        return add_vocabulary()"""

    clear_screen()
    return training


"""def add_vocabulary():
    # TODO: reincorporate
    clear_screen()
    languages = [language.lower() for language in os.listdir(TrainerBackend.BASE_LANGUAGE_DATA_PATH)]
    print('EXTENSIBLE VOCABULARY FILES: ')
    [print(language) for language in languages]
    selection = resolve_input(input('\nSelect language: ').lower(), languages)
    if selection is None:
        recurse_on_invalid_input(add_vocabulary)
    else:
        sentence_trainer = SentenceTranslationTrainerBackend()
        sentence_trainer._non_english_language = selection
        while True:
            sentence_trainer._append_2_vocabulary_file()
            try:
                procedure_resolution = resolve_input(input("Press Enter to continue adding, otherwise enter 'exit'\t"), ['exit', 'ZUNGENUNMUTSERLABUNG'])
                if procedure_resolution == 'exit':
                    return complete_initialization()
                erase_previous_line()
            except SyntaxError:
                pass"""


def complete_initialization():
    clear_screen()
    display_starting_screen()
    mongo_client = login()
    extended_starting_screen(username=mongo_client.user)
    try:
        display_last_session_statistics(client=mongo_client)
    except KeyError:
        pass

    trainer_frontend = TRAINERS[select_training()]()
    trainer_frontend.relay_database_client_to_backend(mongo_client)
    trainer_frontend.run()

if __name__ == '__main__':
    complete_initialization()
