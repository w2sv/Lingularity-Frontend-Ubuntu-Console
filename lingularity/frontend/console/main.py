from typing import Optional
import os
import time
from getpass import getpass
from functools import partial

from lingularity.frontend.console.trainers import SentenceTranslationTrainerConsoleFrontend, VocableTrainerConsoleFrontend
from lingularity.database import MongoDBClient
from lingularity.utils.input_resolution import recurse_on_unresolvable_input, recurse_on_invalid_input, resolve_input
from lingularity.utils.output_manipulation import clear_screen, erase_lines, centered_print, centered_input_indentation
from lingularity.utils.datetime import is_today_or_yesterday, parse_date_from_string
from lingularity.utils.signup_credential_validation import invalid_mailadress, invalid_password, invalid_username


TRAINERS = {
    'sentence translation': SentenceTranslationTrainerConsoleFrontend,
    'vocabulary trainer': VocableTrainerConsoleFrontend
}


def display_starting_screen():
    clear_screen()
    os.system('wmctrl -r :ACTIVE: -b add,maximized_vert,maximized_horz')
    time.sleep(0.1)

    banner = open(f'{os.path.dirname(os.path.abspath(__file__))}/resources/banner.txt', 'r').read()
    centered_print('\n' * 4, banner, '\n' * 2)
    centered_print("W2SV", '\n')
    centered_print("by Janek Zangenberg ", '\n' * 2)


def authenticate() -> MongoDBClient:
    """ Returns:
            user instantiated client """

    indentation = centered_input_indentation('Enter user name: ')

    username = input(f'{indentation}Enter user name: ')
    if invalid_username(username):
        return recurse_on_invalid_input(authenticate, 'Empty username is not allowed', 2)

    client = MongoDBClient(user=None, language=None)
    if username in client.usernames:
        client.user = username
        password, password_input = client.query_password(), getpass(f'{indentation}Enter password: ')
        while password != password_input:
            erase_lines(1)
            password_input = getpass(f'{indentation}Incorrect, try again: ')
        erase_lines(2)

    else:
        erase_lines(1)
        sign_up(username, client, indentation)

    return client

def sign_up(user: str, client: MongoDBClient, indentation: str, email_address: Optional[str] = None):
    args = list(locals().values())
    _recurse_on_invalid_input = partial(recurse_on_invalid_input,
                                        func=sign_up)

    centered_print('Create a new account\n')

    email_query = 'Enter email address: '
    if email_address is not None:
        print(f'{indentation}{email_query}{email_address}')
    else:
        email_address = input(f'{indentation}{email_query}')
        if invalid_mailadress(email_address):
            return _recurse_on_invalid_input(message='Invalid email address', n_deletion_lines=4, args=args)
        """elif client.mail_address_taken(mail_address):
            return _recurse_on_invalid_input(message='Email address taken')"""

    password = getpass(f'{indentation}Create password: ')
    if invalid_password(password):
        return _recurse_on_invalid_input(message='Password must contain at least 5 characters', n_deletion_lines=5, args=args[:-1] + [email_address])

    client.user = user
    client.initialize_user(email_address, password)
    erase_lines(4)


def extended_starting_screen(username: str):
    centered_print("         Sentence data stemming from the Tatoeba Project to be found at http://www.manythings.org/anki", '\n' * 2)
    centered_print("Note: all requested inputs may be merely entered up to a point which allows for an unambigious identification of the intended choice,")
    centered_print("  e.g. 'it' suffices for selecting Italian since there's no other eligible language starting on 'it'", '\n' * 2)
    centered_print(f"What's up {username}?", '\n' * 2)


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
    in_between_indentation = '\t' * 2
    input_message = f"What would you like to do?: {in_between_indentation}Translate (S)entences{in_between_indentation}Train (V)ocabulary{in_between_indentation}or (A)dd Vocabulary\n"
    indentation = centered_input_indentation(input_message)
    training = resolve_input(input(indentation + input_message).lower(), list(TRAINERS.keys()) + ['add vocabulary'])

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
        return recurse_on_unresolvable_input(add_vocabulary)
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
    mongo_client = authenticate()
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
