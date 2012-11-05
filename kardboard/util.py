from datetime import datetime


def now():
    return datetime.now()


def relativedelta(*args, **kwargs):
    from dateutil.relativedelta import relativedelta
    return relativedelta(*args, **kwargs)


def delta_in_hours(delta):
    try:
        seconds = delta.total_seconds()
    except AttributeError:
        # We're in pythont 2.6
        seconds = delta.seconds
        days = delta.days
        seconds = seconds + (days * 24 * 60 * 60)

    hours = (seconds / 60.0) / 60.0
    hours = round(hours)
    return hours
