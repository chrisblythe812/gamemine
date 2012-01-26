import calendar
from datetime import datetime, date, timedelta


def inc_months(d, value, specifying_date=None):
    """
    Adds `value` of months to the date `d`. If `specifying_date` is passed, the day of resulting month
    will be taken from the `specifying_date` instead of `d`.

    `value` can be str or int, e. g. "10d", "1m", "-20d", 5.
    If it's int assuming that value is number of months.

    >>> inc_months(datetime(2010, 3, 31), 0)
    datetime.datetime(2010, 3, 31, 0, 0)

    >>> inc_months(datetime(2010, 3, 31), 23)
    datetime.datetime(2012, 2, 29, 0, 0)

    >>> inc_months(datetime(2010, 2, 28), 1, datetime(2010, 1, 31))
    datetime.datetime(2010, 3, 31, 0, 0)

    >>> inc_months(datetime(2010, 3, 31), -3)
    datetime.datetime(2009, 12, 31, 0, 0)

    >>> inc_months(datetime(2010, 3, 31), "-3m")
    datetime.datetime(2009, 12, 31, 0, 0)

    >>> inc_months(datetime(2010, 1, 1), "3d")
    datetime.datetime(2010, 1, 4, 0, 0)

    >>> inc_months(datetime(2010, 1, 4), "-3d")
    datetime.datetime(2010, 1, 1, 0, 0)
    """
    if isinstance(value, str):
        if value[-1:] == "m":
            value = int(value[:-1])
        elif value[-1:] == "d":
            value = int(value[:-1])
            return d + timedelta(value)
        else:
            raise ValueError
    assert(isinstance(d, (date, datetime)))
    assert(isinstance(value, int))
    if specifying_date:
        assert(isinstance(specifying_date, (date, datetime)))

    d0 = d.replace(day=1)
    years, months = value / 12, value % 12
    if d0.month + months > 12:
        years += 1
        months = months - 12
    d0 = d0.replace(year=d0.year + years, month=d0.month + months)
    max_day = calendar.monthrange(d0.year, d0.month)[1]
    day = min(max_day, (specifying_date or d).day)
    return d0.replace(day=day)


inc_date = inc_months
