from typing import Tuple
import getpass

from backend import MongoDBClient

from frontend.utils import query, view
from frontend.screen.authentication._utils import authentication_screen, HORIZONTAL_INDENTATION


@view.creator(title='Login', banner='lingularity/isometric2', banner_color='blue')
@authentication_screen
def __call__() -> Tuple[str, bool]:
    """ Returns:
            username: str,
            is_new_user_flag: bool """

    horizontal_indentation = HORIZONTAL_INDENTATION
    mongodb_client = MongoDBClient.get_instance()

    username = query.relentlessly(f'{horizontal_indentation}Enter username: ', correctness_verifier=lambda response: response in mongodb_client.usernames, error_indication_message='ENTERED MAILADDRESS NOT ASSOCIATED WITH AN ACCOUNT', sleep_duration=1.5)
    query.relentlessly(f'{horizontal_indentation}Enter password: ', correctness_verifier=lambda response: response == mongodb_client.query_password(username), error_indication_message='INCORRECT, TRY AGAIN', query_method=getpass.getpass, sleep_duration=1.5)

    return username, False
