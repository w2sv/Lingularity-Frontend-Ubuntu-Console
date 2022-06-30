from typing import Tuple, Optional

from backend.src.database import UserTranscendentMongoDBClient

from frontend.src.utils import query
from frontend.src.utils import view
from frontend.src.screen.authentication._utils import authentication_screen_renderer, HORIZONTAL_INDENTATION


@view.creator(title='Login', banner_args=('lingularity/isometric1', 'red'))
@authentication_screen_renderer
@UserTranscendentMongoDBClient.receiver
def __call__(user_transcendent_mongodb: UserTranscendentMongoDBClient) -> Optional[Tuple[str, bool]]:
    """ Returns:
            username: str,
            is_new_user_flag: bool """

    horizontal_indentation = HORIZONTAL_INDENTATION

    if (username := query.relentlessly(f'{horizontal_indentation}Enter username: ',
                                       applicability_verifier=lambda response: response in user_transcendent_mongodb.usernames,
                                       error_indication_message='ENTERED MAILADDRESS NOT ASSOCIATED WITH AN ACCOUNT',
                                       sleep_duration=1.5, cancelable=True)) == query.CANCELLED:
        return None

    elif query.relentlessly(f'{horizontal_indentation}Enter password: ',
                            applicability_verifier=lambda response: response == user_transcendent_mongodb.query_password(username),
                            error_indication_message='INCORRECT, TRY AGAIN', sleep_duration=1.5, cancelable=True) == query.CANCELLED:
        return None

    return username, False
