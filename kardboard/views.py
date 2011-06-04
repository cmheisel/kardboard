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
        scope = 'year'
    if month:
        scope = 'month'
    if day:
        scope = 'day'

    if not year:
        year = date.year
    if not month:
        month = date.month
    if not day:
        day = date.day

    cards = Kard.in_progress.all()
    cards = sorted(cards, key=lambda c: c.current_cycle_time())
    cards.reverse()

    metrics = [
        {'Ave. Cycle Time': Kard.objects.moving_cycle_time(
            year=year, month=month, day=day)},
        {'Done this week': Kard.objects.done_in_week(
            year=year, month=month, day=day).count()},
        {'Done this month':
            Kard.objects.done_in_month(
                year=year, month=month).count()},
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
