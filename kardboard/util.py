import datetime


def business_days_between(date1, date2):
    if date1 < date2:
        oldest_date, youngest_date = date1, date2
    else:
        oldest_date, youngest_date = date2, date1

    business_days = 0
    date = oldest_date
    while date < youngest_date:
        if date.weekday() != 5 and date.weekday() != 6:
            business_days += 1
        date = date + datetime.timedelta(days=1)
    return business_days
