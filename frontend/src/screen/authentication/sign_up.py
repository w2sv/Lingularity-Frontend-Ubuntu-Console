from typing import Tuple, Optional

from backend.database import UserTranscendentMongoDBClient

from frontend.src.utils import query
from frontend.src.utils import view
from frontend.src.screen.authentication._utils import authentication_screen_renderer, HORIZONTAL_INDENTATION


@view.creator(title='Sign Up', banner_args=('lingularity/isometric2', 'red'))
@authentication_screen_renderer
def __call__() -> Optional[Tuple[str, bool]]:
    """ Returns:
            username: str,
            is_new_user_flag: bool """

    if (mail_address := query.relentlessly(
            f'{HORIZONTAL_INDENTATION}Enter mailaddress: ',
            applicability_verifier=_is_valid_mail_address,
            error_indication_message='INVALID EMAIL ADDRESS', cancelable=True
    )) == query.CANCELLED:
        return None

    elif (username := query.relentlessly(
            f'{HORIZONTAL_INDENTATION}Create username: ',
            applicability_verifier=_is_valid_username,
            error_indication_message='EMPTY USERNAME NOT ALLOWED', cancelable=True
    )) == query.CANCELLED:
        return None

    elif (password := query.relentlessly(
            f'{HORIZONTAL_INDENTATION}Create password: ',
            applicability_verifier=_is_valid_password,
            error_indication_message='PASSWORD HAS TO COMPRISE AT LEAST 5 CHARACTERS',
            cancelable=True
    )) == query.CANCELLED:
        return None

    elif query.relentlessly(
            f'{HORIZONTAL_INDENTATION}Confirm password: ',
            applicability_verifier=lambda password_confirmation: password_confirmation == password,
            error_indication_message="PASSWORDS DON'T MATCH", cancelable=True
    ) == query.CANCELLED:
        return None

    UserTranscendentMongoDBClient.instance().initialize_user(
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