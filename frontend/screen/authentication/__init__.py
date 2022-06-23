from backend import MongoDBClient

from frontend import logged_in_user
from frontend.state import State
from frontend.screen.authentication import front as front_screen


def __call__():
    """ Attempts to retrieve locally cashed user,
        if unfeasible proceeds to front screen into
        either log in/sign up

        Inserts user, is_new_user flag into State, mongodb client """

    mongodb_client = MongoDBClient.instance()
    is_new_user = False

    # try to retrieve logged in user from disk
    if (username := logged_in_user.retrieve()) is None:
        username, is_new_user = front_screen.__call__()

        # store username in encrypted manner
        logged_in_user.store(username=username)

    assert username is not None

    # set state, database variables
    mongodb_client.user = username
    State.set_user(username, is_new_user=is_new_user)
