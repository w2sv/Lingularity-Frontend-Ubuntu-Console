from backend import MongoDBClient

from frontend.utils import query, output, view
from frontend.reentrypoint import ReentryPoint
from frontend import locally_cashed_user


@view.creator(banner_args=('lingularity/impossible', 'yellow'))
def __call__() -> ReentryPoint:
    print(output.row_percentual_indentation(percentage=0.15))

    output.centered(f'Are you sure you want to irreversibly delete your account? {query.YES_NO_QUERY_OUTPUT}')
    if query.relentlessly('', indentation_percentage=0.5, options=query.YES_NO_OPTIONS) == 'yes':
        MongoDBClient.get_instance().remove_user()
        locally_cashed_user.remove()
        return ReentryPoint.Exit
    return ReentryPoint.Home
