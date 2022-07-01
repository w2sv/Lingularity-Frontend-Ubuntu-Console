from backend.src.database import UserMongoDBClient

from frontend.src.utils import prompt, output
from frontend.src.utils import view
from frontend.src.reentrypoint import ReentryPoint
from frontend.src import logged_in_user
from frontend.src.utils.prompt.repetition import prompt_relentlessly
from frontend.src.utils.view import Banner


@view.creator(banner=Banner('lingularity/impossible', 'yellow'))
def __call__() -> ReentryPoint:
    print(output.row_percentual_indentation(percentage=0.15))

    output.centered(f'Are you sure you want to irreversibly delete your account? {prompt.YES_NO_QUERY_OUTPUT}')
    if prompt_relentlessly('', indentation_percentage=0.5, options=prompt.YES_NO_OPTIONS) == 'yes':
        UserMongoDBClient.instance().remove_user()
        logged_in_user.remove()
        return ReentryPoint.Exit
    return ReentryPoint.Home
