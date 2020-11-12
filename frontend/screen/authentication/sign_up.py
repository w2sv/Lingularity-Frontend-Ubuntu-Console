from typing import Tuple
from backend import MongoDBClient
import getpass

from frontend.utils import query, view
from frontend.screen.authentication._utils import compute_vertical_indentation, compute_horizontal_indentation


@view.creator(title='Sign Up', banner='lingularity/isometric2', banner_color='blue')
def __call__() -> Tuple[str, bool]:
    print(compute_vertical_indentation())

    horizontal_indentation = compute_horizontal_indentation()
    mailaddress = query.relentlessly(f'{horizontal_indentation}Enter mailaddress: ', correctness_verifier=_is_valid_mailaddress, error_indication_message='INVALID EMAIL ADDRESS')
    username = query.relentlessly(f'{horizontal_indentation}Create username: ', correctness_verifier=_is_valid_username, error_indication_message='EMPTY USERNAME NOT ALLOWED')
    password = query.relentlessly(f'{horizontal_indentation}Create password: ', correctness_verifier=_is_valid_password, error_indication_message='PASSWORD HAS TO COMPRISE AT LEAST 5 CHARACTERS', query_method=getpass.getpass)
    query.relentlessly(f'{horizontal_indentation}Confirm password: ', correctness_verifier=lambda password_confirmation: password_confirmation == password, error_indication_message="PASSWORDS DON'T MATCH", query_method=getpass.getpass)

    MongoDBClient.get_instance().initialize_user(user=username, email_address=mailaddress, password=password)
    return username, True


def _is_valid_mailaddress(mailaddress: str) -> bool:
    MIN_MAILADDRESS_LENGTH = 3

    return '@' in mailaddress and len(mailaddress.strip()) >= MIN_MAILADDRESS_LENGTH


def _is_valid_username(username: str) -> bool:
    return bool(len(username.strip()))


def _is_valid_password(password: str) -> bool:
    MIN_PASSWORD_LENGTH = 5

    return len(password) >= MIN_PASSWORD_LENGTH
