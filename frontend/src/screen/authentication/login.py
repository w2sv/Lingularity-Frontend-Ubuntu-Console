from typing import Optional, Tuple

from backend.src.database.credentials_database import CredentialsDatabase

from frontend.src.screen.authentication._utils import authentication_screen, HORIZONTAL_INDENTATION
from frontend.src.utils import view
from frontend.src.utils.prompt.cancelling import QUERY_CANCELLED
from frontend.src.utils.prompt.repetition import prompt_relentlessly
from frontend.src.utils.view import Banner


@view.creator(title='Login', banner=Banner('lingularity/isometric1', 'red'))
@authentication_screen
@CredentialsDatabase.receiver
def __call__(credentials_database: CredentialsDatabase) -> Optional[Tuple[str, bool]]:
    """ Returns:
            username: str,
            is_new_user_flag: bool """

    horizontal_indentation = HORIZONTAL_INDENTATION

    if (username := prompt_relentlessly(
            f'{horizontal_indentation}Enter username: ',
            applicability_verifier=lambda response: response in credentials_database.usernames,
            error_indication_message='ENTERED MAIL ADDRESS NOT ASSOCIATED WITH AN ACCOUNT',
            sleep_duration=1.5, cancelable=True
    )) == QUERY_CANCELLED:
        return None

    elif prompt_relentlessly(
            f'{horizontal_indentation}Enter password: ',
            applicability_verifier=lambda response: response == credentials_database.query_password(username),
            error_indication_message='INCORRECT, TRY AGAIN', sleep_duration=1.5, cancelable=True
    ) == QUERY_CANCELLED:
        return None

    return username, False