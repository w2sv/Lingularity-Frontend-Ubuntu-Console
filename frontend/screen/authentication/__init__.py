from typing import Optional
import os

from backend import MongoDBClient

from frontend.state import State
from frontend.utils import fernet
from frontend.screen.ops import USER_ENCRYPTION_FILE_PATH
from frontend.screen.authentication import front as front_screen


def __call__():
    mongodb_client = MongoDBClient.get_instance()
    is_new_user = False

    # try to retrieve logged in user from disk
    if (username := _retrieve_logged_in_user_from_disk()) is None:
        username, is_new_user = front_screen.__call__()

        # store username in encrypted manner
        _store_logged_in_user(username)

    assert username is not None

    # set state, database variables
    mongodb_client.user = username
    State.set_user(username, is_new_user=is_new_user)


def _retrieve_logged_in_user_from_disk() -> Optional[str]:
    if not os.path.exists(USER_ENCRYPTION_FILE_PATH):
        return None
    return fernet.decrypt(open(USER_ENCRYPTION_FILE_PATH, 'rb').read())


def _store_logged_in_user(username: str):
    with open(USER_ENCRYPTION_FILE_PATH, 'wb+') as user_encryption_file:
        user_encryption_file.write(fernet.encrypt(username))
