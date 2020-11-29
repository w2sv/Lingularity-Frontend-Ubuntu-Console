from backend import MongoDBClient

from frontend import locally_cashed_user
from frontend.state import State
from frontend.screen.authentication import front as front_screen


def __call__():
    mongodb_client = MongoDBClient.get_instance()
    is_new_user = False

    # try to retrieve logged in user from disk
    if (username := locally_cashed_user.retrieve()) is None:
        username, is_new_user = front_screen.__call__()

        # store username in encrypted manner
        locally_cashed_user.store(username=username)

    assert username is not None

    # set state, database variables
    mongodb_client.user = username
    State.set_user(username, is_new_user=is_new_user)
