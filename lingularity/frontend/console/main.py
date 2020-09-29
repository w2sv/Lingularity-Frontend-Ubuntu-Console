from typing import Optional, Dict, Union, Callable, Any
import os
import time
from getpass import getpass
from functools import partial
import requests
import sys
import random
import logging

import cursor

from lingularity.backend.database import MongoDBClient
from lingularity.backend.ops.google.translation import GoogleTranslation
from lingularity.frontend.console.utils.input_resolution import recurse_on_unresolvable_input, recurse_on_invalid_input, resolve_input
from lingularity.frontend.console.utils.date import today_or_yesterday, string_date_2_datetime_type
from lingularity.frontend.console.utils.signup_credential_validation import invalid_mailadress, invalid_password, invalid_username
from lingularity.frontend.console.utils.user_login_storage import (get_logged_in_user, write_fernet_key_if_not_existent,
                                                                   store_user_login, USER_ENCRYPTION_FILE_PATH)
from lingularity.frontend.console.utils.output import (clear_screen, erase_lines, centered_print,
                                                       get_centered_input_query_indentation,
                                                       DEFAULT_VERTICAL_VIEW_OFFSET)


def display_starting_screen():
    clear_screen()
    os.system('wmctrl -r :ACTIVE: -b add,maximized_vert,maximized_horz && wmctrl -r :ACTIVE: -N "Lingularity - Acquire Languages the Litboy Way"')
    time.sleep(0.1)

    banner = open(f'{os.path.dirname(os.path.abspath(__file__))}/resources/banner.txt', 'r').read()
    centered_print(DEFAULT_VERTICAL_VIEW_OFFSET * 2, banner, '\n' * 2)
    centered_print("W2SV", '\n')

try:
    from lingularity.frontend.console.trainers import (SentenceTranslationTrainerConsoleFrontend,
                                                       VocableTrainerConsoleFrontend,
                                                       TrainerConsoleFrontend,
                                                       VocableAdderFrontend)
    from lingularity.backend.ops import google
except (RuntimeError, requests.exceptions.ConnectionError):
    display_starting_screen()
    centered_print(
        '\nLingularity relies on an internet connection in order to retrieve and store data. Please establish one and restart the program.\n\n')
    cursor.hide()
    time.sleep(5)
    cursor.show()
    sys.exit(0)


logging.basicConfig(filename='logging.txt', level=logging.INFO)


def assign_client_user_from_existing_login(mongodb_client) -> bool:
    if (logged_in_user := get_logged_in_user()) is not None and logged_in_user in mongodb_client.usernames:
        mongodb_client.user = logged_in_user
        return True
    return False


def authenticate(mongodb_client) -> MongoDBClient:
    """ Returns:
            user instantiated mongodb client
            new_login: bool """

    INDENTATION = get_centered_input_query_indentation('Enter user name: ')

    username = input(f'{INDENTATION}Enter user name: ')
    if invalid_username(username):
        return recurse_on_invalid_input(authenticate, message='Empty username is not allowed', n_deletion_lines=2)

    if username in mongodb_client.usernames:
        mongodb_client.user = username
        password, password_input = mongodb_client.query_password(), getpass(f'{INDENTATION}Enter password: ')
        while password != password_input:
            print('')
            erase_lines(2)
            password_input = getpass(f'{INDENTATION}Incorrect, try again: ')
        erase_lines(2)

    else:
        erase_lines(1)
        sign_up(username, mongodb_client, INDENTATION)

    write_fernet_key_if_not_existent()
    store_user_login(username)

    return mongodb_client


def sign_up(user: str, client: MongoDBClient, indentation: str, email_address: Optional[str] = None):
    args = list(locals().values())
    _recurse_on_invalid_input = partial(recurse_on_invalid_input, function=sign_up)

    centered_print('Create a new account\n')

    email_query = 'Enter email address: '
    if email_address is not None:
        print(f'{indentation}{email_query}{email_address}')
    else:
        email_address = input(f'{indentation}{email_query}')
        if invalid_mailadress(email_address):
            return _recurse_on_invalid_input(message='Invalid email address', n_deletion_lines=4, func_args=args)
        """elif client.mail_address_taken(mail_address):
            return _recurse_on_invalid_input(message='Email address taken')"""

    password = getpass(f'{indentation}Create password: ')
    if invalid_password(password):
        return _recurse_on_invalid_input(message='Password must contain at least 5 characters', n_deletion_lines=5, args=args[:-1] + [email_address])

    client.user = user
    client.initialize_user(email_address, password)
    erase_lines(4)


def change_account():
    os.remove(USER_ENCRYPTION_FILE_PATH)
    del ELIGIBLE_ACTIONS['change account']
    return complete_initialization()


def extended_starting_screen(username: str, latest_trained_language: Optional[str]):
    CONSECUTIVE_VERTICAL_SPACE = '\n' * 2

    centered_print("Sentence data stemming from the Tatoeba Project to be found at http://www.manythings.org/anki", '\n' * 2)
    centered_print("Note: all requested inputs may be merely entered up to a point which allows for an unambigious identification of the intended choice,")
    centered_print("e.g. 'it' suffices for selecting Italian since there's no other eligible language starting on 'it'", '\n' * 2)

    constitution_query = random.choice([f"What's up", f"How are you"]) + f' {username.title()}?'
    if latest_trained_language is not None and (language_identifier := GoogleTranslation().get_identifier(latest_trained_language)) is not None:
        constitution_query_translation = GoogleTranslation().translate(constitution_query, src='en', dest=language_identifier)
        centered_print(constitution_query_translation, CONSECUTIVE_VERTICAL_SPACE)
    else:
        centered_print(constitution_query, CONSECUTIVE_VERTICAL_SPACE)


def display_last_session_statistics(last_session_metrics: Optional[Dict[str, Any]]):
    if last_session_metrics is None:
        return

    last_session_items = 'vocables' if last_session_metrics['trainer'] == 'v' else 'sentences'

    if (toy := today_or_yesterday(string_date_2_datetime_type(last_session_metrics['date']))) is not None:
        date_repr = toy
    else:
        parsed_date = string_date_2_datetime_type(last_session_metrics['date'])
        date_repr = f'the {parsed_date.day}th of {parsed_date.strftime("%B")} {parsed_date.year}'

    centered_print(f"You faced {last_session_metrics['nFacedItems']} {last_session_metrics['language']} {last_session_items} during your last session {date_repr}\n\n")


def select_action() -> Optional[str]:
    in_between_indentation = ' ' * 6
    input_message = f"What would you like to do?: {in_between_indentation}Translate (S)entences{in_between_indentation}Train (V)ocabulary{in_between_indentation}(A)dd Vocabulary{in_between_indentation}(C)hange Account\n"
    centered_print(input_message, ' ', end='')
    training = resolve_input('', list(ELIGIBLE_ACTIONS.keys()))

    if training is None:
        return recurse_on_unresolvable_input(select_action, n_deletion_lines=4)

    clear_screen()
    return training


ELIGIBLE_ACTIONS: Dict[str, Union[type, Callable]] = {
    'sentence translation': SentenceTranslationTrainerConsoleFrontend,
    'vocabulary trainer': VocableTrainerConsoleFrontend,
    'add vocabulary': VocableAdderFrontend,
    'change account': change_account
}


def complete_initialization():
    mongodb_client = MongoDBClient()
    client_user_set = assign_client_user_from_existing_login(mongodb_client)

    clear_screen()
    display_starting_screen()

    if not client_user_set:
        mongodb_client = authenticate(mongodb_client)

    if (last_session_metrics := mongodb_client.query_last_session_statistics()) is not None:
        extended_starting_screen(username=mongodb_client.user, latest_trained_language=last_session_metrics['language'])
        display_last_session_statistics(last_session_metrics=last_session_metrics)
    else:
        extended_starting_screen(username=mongodb_client.user, latest_trained_language=None)

    action_selection: str = select_action()
    action_executor = ELIGIBLE_ACTIONS[action_selection]

    if isinstance(action_executor, type):
        action_executor(mongodb_client).run()
        if action_executor is VocableAdderFrontend:
            return complete_initialization()
    else:
        return action_executor()


if __name__ == '__main__':
    complete_initialization()
