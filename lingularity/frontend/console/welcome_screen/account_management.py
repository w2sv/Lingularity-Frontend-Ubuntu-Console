from typing import Optional
from getpass import getpass
import os

from lingularity.backend.database import MongoDBClient
from lingularity.frontend.console.utils.input_resolution import recurse_on_invalid_input
from lingularity.frontend.console.utils.output import centered_user_query_indentation, erase_lines, centered_print
from lingularity.frontend.console.utils import credentials
from lingularity.frontend.console.utils import fernet


USER_ENCRYPTION_FILE_PATH = f'{os.getcwd()}/.logged_in_user'


def retrieve_logged_in_user_from_disk() -> Optional[str]:
    if not os.path.exists(USER_ENCRYPTION_FILE_PATH):
        return None

    return fernet.decrypt(open(USER_ENCRYPTION_FILE_PATH, 'rb').read())


def _store_logged_in_user(username: str):
    with open(USER_ENCRYPTION_FILE_PATH, 'wb+') as user_encryption_file:
        user_encryption_file.write(fernet.encrypt(username))


def log_in(mongodb_client: MongoDBClient) -> MongoDBClient:
    """ Returns:
            user instantiated mongodb client """

    USER_NAME_QUERY = 'Enter user name: '
    INDENTATION = centered_user_query_indentation(USER_NAME_QUERY)

    # query username
    username = input(f'{INDENTATION}{USER_NAME_QUERY}')
    if credentials.invalid_username(username):
        return recurse_on_invalid_input(log_in, message='Empty username is not allowed', n_deletion_lines=2)

    # query password if entered username existent
    if username in mongodb_client.usernames:
        mongodb_client.user = username

        def query_password(message: str) -> str:
            return getpass(f'{INDENTATION}{message}')

        password, password_input = mongodb_client.query_password(), query_password('Enter password: ')
        while password != password_input:
            erase_lines(1)
            password_input = query_password('Incorrect, try again: ')
        erase_lines(2)

    # otherwise create new account
    else:
        erase_lines(1)
        _sign_up(username, mongodb_client, INDENTATION)

    # store encrypted user
    if not fernet.key_existent():
        fernet.write_key()
    _store_logged_in_user(username)

    return mongodb_client


def _sign_up(user: str, client: MongoDBClient, indentation: str, email_address: Optional[str] = None):
    EMAIL_QUERY = 'Enter email address: '

    centered_print('Create a new account\n')

    if email_address is not None:
        print(f'{indentation}{EMAIL_QUERY}{email_address}')
    else:
        email_address = input(f'{indentation}{EMAIL_QUERY}')

        if credentials.invalid_mailaddress(email_address):
            return recurse_on_invalid_input(
                message='Invalid email address',
                n_deletion_lines=4,
                function=_sign_up,
                args=(user, client, indentation, None)
            )

        # TODO
        """elif client.mail_address_taken(mail_address):
            return _recurse_on_invalid_input(message='Email address taken')"""

    password = getpass(f'{indentation}Create password: ')

    if credentials.invalid_password(password):
        return recurse_on_invalid_input(
            message='Password must contain at least 5 characters',
            n_deletion_lines=5,
            function=_sign_up,
            args=(user, client, indentation, email_address)
        )

    client.initialize_user(user, email_address=email_address, password=password)
    erase_lines(4)


def change_account(eligible_actions) -> bool:
    """ Returns:
            program_reinitialization_flag """

    os.remove(USER_ENCRYPTION_FILE_PATH)
    del eligible_actions['change account']
    return True
