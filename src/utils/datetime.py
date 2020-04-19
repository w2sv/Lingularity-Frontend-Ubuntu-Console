from typing import Optional
import datetime


def parse_date(date: str) -> datetime.date:
    return datetime.datetime.strptime(date, '%Y-%m-%d').date()


def n_days_ago(date: str) -> int:
    return (datetime.date.today() - parse_date(date)).days


def today_or_yesterday(date: datetime.date) -> Optional[str]:
    today = datetime.datetime.today().date()
    if date == today:
        return 'today'
    elif (today - date).days == 1:
        return 'yesterday'
    else:
        return None
