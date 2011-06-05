import datetime

from flask import render_template

from kardboard import app, __version__
from kardboard.models import Kard


@app.route('/')
@app.route('/<int:year>/<int:month>/')
@app.route('/<int:year>/<int:month>/<int:day>/')
def dashboard(year=None, month=None, day=None):
    date = datetime.datetime.now()
    scope = 'current'

    if year:
        date = date.replace(year=year)
        scope = 'year'
    if month:
        date = date.replace(month=month)
        scope = 'month'
    if day:
        date = date.replace(day=day)
        scope = 'day'

    cards = list(Kard.in_progress(date))
    cards = sorted(cards, key=lambda c: c.current_cycle_time(date))
    cards.reverse()

    metrics = [
        {'Ave. Cycle Time': Kard.objects.moving_cycle_time(
            year=date.year, month=date.month, day=date.day)},
        {'Done this week': Kard.objects.done_in_week(
            year=date.year, month=date.month, day=date.day).count()},
        {'Done this month':
            Kard.objects.done_in_month(
                year=date.year, month=date.month).count()},
        {'Work in progress': len(cards)},
    ]

    title = "Dashboard"
    if scope == 'year':
        title += " for %s"
    if scope == 'month':
        title += " for %s/%s" % (date.month, date.year)
    if scope == 'day' or scope == 'current':
        title += " for %s/%s/%s" % (date.month, date.day, date.year)

    context = {
        'scope': scope,
        'date': date,
        'title': title,
        'metrics': metrics,
        'cards': cards,
        'updated_at': datetime.datetime.now(),
        'version': __version__,
    }

    return render_template('dashboard.html', **context)
