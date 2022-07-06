from __future__ import annotations

from backend.src.database.credentials_database import CredentialsDatabase

from frontend.src.screen.authentication._utils import authentication_screen, HORIZONTAL_INDENTATION
from frontend.src.utils import view
from frontend.src.utils.prompt.cancelling import QUERY_CANCELLED
from frontend.src.utils.prompt.repetition import prompt_relentlessly
from frontend.src.utils.view import Banner


@view.creator(title='Sign Up', banner=Banner('lingularity/isometric2', 'red'))
@authentication_screen
@CredentialsDatabase.receiver
def __call__(credentials_database: CredentialsDatabase) -> tuple[str, bool] | None:
    """ Returns:
            username: str,
            is_new_user_flag: bool """

    if (mail_address := prompt_relentlessly(
            f'{HORIZONTAL_INDENTATION}Enter mailaddress: ',
            applicability_verifier=_is_valid_mail_address,
            error_indication_message='INVALID EMAIL ADDRESS', cancelable=True
    )) == QUERY_CANCELLED:
        return None

    elif (username := prompt_relentlessly(
            f'{HORIZONTAL_INDENTATION}Create username: ',
            applicability_verifier=_is_valid_username,
            error_indication_message='EMPTY USERNAME NOT ALLOWED', cancelable=True
    )) == QUERY_CANCELLED:
        return None

    elif (password := prompt_relentlessly(
            f'{HORIZONTAL_INDENTATION}Create password: ',
            applicability_verifier=_is_valid_password,
            error_indication_message='PASSWORD HAS TO COMPRISE AT LEAST 5 CHARACTERS',
            cancelable=True
    )) == QUERY_CANCELLED:
        return None

    elif prompt_relentlessly(
            f'{HORIZONTAL_INDENTATION}Confirm password: ',
            applicability_verifier=lambda password_confirmation: password_confirmation == password,
            error_indication_message="PASSWORDS DON'T MATCH", cancelable=True
    ) == QUERY_CANCELLED:
        return None

    credentials_database.initialize_user(
        username=username,
        email_address=mail_address,
        password=password
    )
    return username, True


def _is_valid_mail_address(mail_address: str) -> bool:
    MIN_MAIL_ADDRESS_LENGTH = 3

    return '@' in mail_address and len(mail_address.strip()) >= MIN_MAIL_ADDRESS_LENGTH


def _is_valid_username(username: str) -> bool:
    return bool(len(username.strip()))


def _is_valid_password(password: str) -> bool:
    MIN_PASSWORD_LENGTH = 5

    return len(password) >= MIN_PASSWORD_LENGTH