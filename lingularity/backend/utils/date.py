import datetime


def todays_date_tag() -> str:
    """ Returns:
            date tag, e.g. 2020-08-12 """

    return str(datetime.date.today())


def n_days_ago(date: str) -> int:
    return (datetime.date.today() - string_date_2_datetime_type(date)).days


def string_date_2_datetime_type(date: str) -> datetime.date:
    return datetime.datetime.strptime(date, '%Y-%m-%d').date()
