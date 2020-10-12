import datetime


def todays_datetag() -> str:
    """ Returns:
            e.g. 2020-08-12 """

    return str(datetime.date.today())


def _string_date_2_datetime_type(date: str) -> datetime.date:
    return datetime.datetime.strptime(date, '%Y-%m-%d').date()


def n_days_ago(date: str) -> int:
    return (datetime.date.today() - _string_date_2_datetime_type(date)).days


def date_repr(date: str) -> str:
    """ Returns:
            'today' if date equals today's date
            'yesterday' if date equaling yesterday's date
            'the {DAY}th of {MONTH} {YEAR}' otherwise """

    converted_date = _string_date_2_datetime_type(date)

    if (today := datetime.datetime.today().date()) == converted_date:
        return 'today'
    elif (today - converted_date).days == 1:
        return 'yesterday'
    else:
        return f'the {converted_date.day}th of {converted_date.strftime("%B")} {converted_date.year}'
