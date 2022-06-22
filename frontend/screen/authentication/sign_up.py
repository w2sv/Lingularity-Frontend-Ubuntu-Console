from typing import Tuple, Optional
from backend import MongoDBClient
import getpass

from frontend.utils import query, view
from frontend.screen.authentication._utils import authentication_screen, HORIZONTAL_INDENTATION


@view.creator(title='Sign Up', banner_args=('lingularity/isometric2', 'red'))
@authentication_screen
def __call__() -> Optional[Tuple[str, bool]]:
    """ Returns:
            username: str,
            is_new_user_flag: bool """

    if (mailaddress := query.relentlessly(f'{HORIZONTAL_INDENTATION}Enter mailaddress: ',
                                          applicability_verifier=_is_valid_mailaddress,
                                          error_indication_message='INVALID EMAIL ADDRESS', cancelable=True)) == query.CANCELLED:
        return None

    elif (username := query.relentlessly(f'{HORIZONTAL_INDENTATION}Create username: ',
                                         applicability_verifier=_is_valid_username,
                                         error_indication_message='EMPTY USERNAME NOT ALLOWED', cancelable=True)) == query.CANCELLED:
        return None

    elif (password := query.relentlessly(f'{HORIZONTAL_INDENTATION}Create password: ',
                                         applicability_verifier=_is_valid_password,
                                         error_indication_message='PASSWORD HAS TO COMPRISE AT LEAST 5 CHARACTERS',
                                         cancelable=True)) == query.CANCELLED:
        return None

    elif query.relentlessly(f'{HORIZONTAL_INDENTATION}Confirm password: ',
                            applicability_verifier=lambda password_confirmation: password_confirmation == password,
                            error_indication_message="PASSWORDS DON'T MATCH", cancelable=True) == query.CANCELLED:
        return None

    MongoDBClient.instance().initialize_user(user=username, email_address=mailaddress, password=password)
    return username, True


def _is_valid_mailaddress(mailaddress: str) -> bool:
    MIN_MAILADDRESS_LENGTH = 3

    return '@' in mailaddress and len(mailaddress.strip()) >= MIN_MAILADDRESS_LENGTH


def _is_valid_username(username: str) -> bool:
    return bool(len(username.strip()))


def _is_valid_password(password: str) -> bool:
    MIN_PASSWORD_LENGTH = 5

    return len(password) >= MIN_PASSWORD_LENGTH
