from backend.src.database.credentials_database import CredentialsDatabase

from frontend.src.state import State
from frontend.src.utils import prompt, output
from frontend.src.utils import view
from frontend.src.reentrypoint import ReentryPoint
from frontend.src import logged_in_user
from frontend.src.utils.prompt.repetition import prompt_relentlessly
from frontend.src.utils.view import Banner


@view.creator(banner=Banner('lingularity/impossible', 'yellow'))
@State.receiver
def __call__(state: State) -> ReentryPoint:
    print(output.row_percentual_indentation(percentage=0.15))

    output.centered(f'Are you sure you want to irreversibly delete your account? {prompt.YES_NO_QUERY_OUTPUT}')
    if prompt_relentlessly('', indentation_percentage=0.5, options=prompt.YES_NO_OPTIONS) == 'yes':
        CredentialsDatabase.instance().remove_user(state.username)
        logged_in_user.remove()
        return ReentryPoint.Exit
    return ReentryPoint.Home
