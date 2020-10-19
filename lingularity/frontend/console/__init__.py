from typing import Dict, Union, Callable
import requests

from lingularity.utils.logging import enable_logging
from lingularity.backend.database import MongoDBClient
from lingularity.frontend.console.utils.output import clear_screen
from lingularity.frontend.console.welcome_screen import (
    account_management,
    display_starting_screen,
    display_additional_information,
    display_welcome_message,
    display_constitution_query,
    display_last_session_conclusion,
    select_action,
    exit_on_missing_internet_connection
)

try:
    from lingularity.frontend.console.trainers import *
except (RuntimeError, requests.exceptions.ConnectionError):
    exit_on_missing_internet_connection()


ELIGIBLE_ACTIONS: Dict[str, Union[type, Callable]] = {
    'sentence translation': SentenceTranslationTrainerConsoleFrontend,
    'vocabulary trainer': VocableTrainerConsoleFrontend,
    'add vocabulary': VocableAdderFrontend,
    'change account': account_management.change_account
}


def _complete_initialization():
    mongodb_client = MongoDBClient()

    # try to retrieve logged in user from disk
    if (logged_in_user := account_management.retrieve_logged_in_user_from_disk()) is not None and logged_in_user in mongodb_client.usernames:
        mongodb_client.user = logged_in_user

    # initialize console
    clear_screen()
    display_starting_screen()

    # log in if user not yet set
    if not mongodb_client.user_set:
        mongodb_client = account_management.log_in(mongodb_client)

    # display additional information, last session metrics if existent
    display_additional_information()
    if (last_session_metrics := mongodb_client.query_last_session_statistics()) is not None:
        display_constitution_query(mongodb_client.user, last_session_metrics['language'])
        display_last_session_conclusion(last_session_metrics=last_session_metrics)
    else:
        display_welcome_message(mongodb_client.user)

    # select action
    action_selection: str = select_action(actions=ELIGIBLE_ACTIONS)
    action_executor = ELIGIBLE_ACTIONS[action_selection]

    # __call__ action
    if isinstance(action_executor, type):
        reinitialize = action_executor(mongodb_client).__call__()
    else:
        reinitialize = action_executor(ELIGIBLE_ACTIONS)

    if reinitialize:
        return _complete_initialization()


if __name__ == '__main__':
    enable_logging()
    _complete_initialization()
