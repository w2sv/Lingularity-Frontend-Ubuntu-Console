from typing import Optional
import datetime


def datetag_today() -> str:
    """ e.g. 2020-08-12 """

    return str(datetime.date.today())


def string_date_2_datetime_type(date: str) -> datetime.date:
    return datetime.datetime.strptime(date, '%Y-%m-%d').date()


def n_days_ago(date: str) -> int:
    return (datetime.date.today() - string_date_2_datetime_type(date)).days


def today_or_yesterday(date: datetime.date) -> Optional[str]:
    """ Returns:
            'today' if date equals today's date
            'yesterday' if date equaling yesterday's date
            None otherwise """

    if (today := datetime.datetime.today().date()) == date:
        return 'today'
    elif (today - date).days == 1:
        return 'yesterday'
    return None
