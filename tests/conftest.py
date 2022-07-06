from backend.src.database import Client, connect_database_client
from backend.src.database.user_database import UserDatabase
import pytest

from frontend.src.state import State


@pytest.fixture(scope='session')
def mongo_client() -> Client:
    return Client(1_500)


@pytest.fixture(scope='session')
def user_database(mongo_client):
    return UserDatabase('test_user', language='Italian')


@pytest.fixture(scope='session')
def state(user_database):
    state = State('test_user', is_new_user=False)
    state.set_language('Italian', train_english=False)
    return state