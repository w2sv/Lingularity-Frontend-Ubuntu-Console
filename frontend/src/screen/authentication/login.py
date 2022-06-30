from typing import Optional, Tuple

from backend.src.database import UserTranscendentMongoDBClient

from frontend.src.screen.authentication._utils import authentication_screen_renderer, HORIZONTAL_INDENTATION
from frontend.src.utils import view
from frontend.src.utils.query.cancelling import QUERY_CANCELLED
from frontend.src.utils.query.repetition import prompt_relentlessly


@view.creator(title='Login', banner_args=('lingularity/isometric1', 'red'))
@authentication_screen_renderer
@UserTranscendentMongoDBClient.receiver
def __call__(user_transcendent_mongodb: UserTranscendentMongoDBClient) -> Optional[Tuple[str, bool]]:
    """ Returns:
            username: str,
            is_new_user_flag: bool """

    horizontal_indentation = HORIZONTAL_INDENTATION

    if (username := prompt_relentlessly(
            f'{horizontal_indentation}Enter username: ',
            applicability_verifier=lambda response: response in user_transcendent_mongodb.usernames,
            error_indication_message='ENTERED MAIL ADDRESS NOT ASSOCIATED WITH AN ACCOUNT',
            sleep_duration=1.5, cancelable=True
    )) == QUERY_CANCELLED:
        return None

    elif prompt_relentlessly(
            f'{horizontal_indentation}Enter password: ',
            applicability_verifier=lambda response: response == user_transcendent_mongodb.query_password(username),
            error_indication_message='INCORRECT, TRY AGAIN', sleep_duration=1.5, cancelable=True
    ) == QUERY_CANCELLED:
        return None

    return username, False