import datetime


today: datetime.date = datetime.date.today()  # e.g. 2020-08-12


def n_days_ago(date: str) -> int:
    """ Args:
            date: format of today value"""

    return (datetime.date.today() - string_2_date(date)).days


def string_2_date(date: str) -> datetime.date:
    """ Args:
            date: format of today value"""

    return datetime.datetime.strptime(date, '%Y-%m-%d').date()
