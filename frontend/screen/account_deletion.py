from backend import MongoDBClient

from frontend.utils import query, output, view
from frontend.reentrypoint import ReentryPoint
from frontend.screen.ops import remove_user_from_disk


@view.creator(banner_args=('lingularity/impossible', 'yellow'))
def __call__() -> ReentryPoint:
    print(output.row_percentual_indentation(percentage=0.15))

    output.centered(f'Are you sure you want to irreversibly delete your account? {query.YES_NO_QUERY_OUTPUT}')
    if query.relentlessly('', options=query.YES_NO_OPTIONS, indentation_percentage=0.5) == 'yes':
        MongoDBClient.get_instance().remove_user()
        remove_user_from_disk()
        return ReentryPoint.Exit
    return ReentryPoint.Home
