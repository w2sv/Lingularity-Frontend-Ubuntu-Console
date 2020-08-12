import calendar
import time


def get_timestamp() -> str:
    """ e.g. 1597228107 """

    return str(calendar.timegm(time.gmtime()))
