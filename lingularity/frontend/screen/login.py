from typing import Optional, Tuple
from getpass import getpass
import os

from lingularity.backend.database import MongoDBClient

from lingularity.frontend.state import State
from lingularity.frontend.utils import credentials, fernet, input_resolution, output, view

_USER_ENCRYPTION_FILE_PATH = f'{os.getcwd()}/.logged_in_user'
_QUERY_INDENTATION = output.centered_print_indentation(' ' * 126)


def remove_user_from_disk():
    os.remove(_USER_ENCRYPTION_FILE_PATH)


# TODO


def __call__() -> bool:
    """ Returns:
            is_new_user_flag: bool """

    mongodb_client = MongoDBClient.get_instance()
    is_new_user = False

    # try to retrieve logged in user from disk
    if (username := _retrieve_logged_in_user_from_disk()) is None:

        # query login credentials
        username, login_successful = _query_login_credentials()

        # sign up new user if entered one not yet existent
        if not login_successful:
            output.erase_lines(1)
            _sign_up(username, mongodb_client, _QUERY_INDENTATION)
            is_new_user = True

    assert username is not None

    # set state, database variables
    mongodb_client.user = username
    State.set_user(username)

    # store encrypted user
    _store_logged_in_user(username)

    return is_new_user


def _retrieve_logged_in_user_from_disk() -> Optional[str]:
    if not os.path.exists(_USER_ENCRYPTION_FILE_PATH):
        return None

    return fernet.decrypt(open(_USER_ENCRYPTION_FILE_PATH, 'rb').read())


def _store_logged_in_user(username: str):
    with open(_USER_ENCRYPTION_FILE_PATH, 'wb+') as user_encryption_file:
        user_encryption_file.write(fernet.encrypt(username))


@view.view_creator(title='Login', banner='lingularity/isometric2', banner_color='blue')
def _query_login_credentials() -> Tuple[str, bool]:
    """ Returns:
            username: str,
            login_successful_flag: bool """

    mongodb_client = MongoDBClient.get_instance()
    login_successful = False

    USER_NAME_QUERY = 'Enter user name: '

    # query username
    username = input(f'{_QUERY_INDENTATION}{USER_NAME_QUERY}')
    if credentials.invalid_username(username):
        return input_resolution.repeat(__call__, n_deletion_lines=2, message='Empty username is not allowed')

    # query password if entered username existent
    elif username in mongodb_client.usernames:
        login_successful = True

        def query_password(message: str) -> str:
            return getpass(f'{_QUERY_INDENTATION}{message}')

        password, password_input = mongodb_client.query_password(username), query_password('Enter password: ')
        while password != password_input:
            # TODO: find way to erase 'Enter password: ' query line, somehow infeasible by means of
            #  erase_lines after first invocation
            output.erase_lines(1)
            password_input = query_password('Incorrect, try again: ')
        output.erase_lines(2)

    return username, login_successful


def _sign_up(user: str, client: MongoDBClient, email_address: Optional[str] = None):
    EMAIL_QUERY = 'Enter email address: '

    output.centered_print('Create a new account\n')

    if email_address is not None:
        print(f'{_QUERY_INDENTATION}{EMAIL_QUERY}{email_address}')
    else:
        email_address = input(f'{_QUERY_INDENTATION}{EMAIL_QUERY}')

        if credentials.invalid_mailaddress(email_address):
            return input_resolution.repeat(function=_sign_up, n_deletion_lines=4, message='Invalid email address',
                                           args=(user, client, _QUERY_INDENTATION, None))

        # TODO
        """elif client.mail_address_taken(mail_address):
            return _recurse_on_invalid_input(message='Email address taken')"""

    password = getpass(f'{_QUERY_INDENTATION}Create password: ')

    if credentials.invalid_password(password):
        return input_resolution.repeat(function=_sign_up, n_deletion_lines=5, message='Password must contain at least 5 characters',
                                       args=(user, client, _QUERY_INDENTATION, email_address))

    client.initialize_user(user, email_address=email_address, password=password)
    output.erase_lines(4)
