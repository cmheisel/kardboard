import datetime

from flask import render_template

from kardboard import app, __version__
from kardboard.models import Kard


@app.route('/')
@app.route('/<int:year>/<int:month>/')
def dashboard(year=None, month=None, day=None):
    now = datetime.datetime.now()
    if not year:
        year = now.year
    if not month:
        month = now.month
    if not day:
        day = now.day

    cards = Kard.in_progress.all()

    metrics = [
        {'Ave. Cycle Time': None},
        {'Done this week': None},
        {'Done this month':
            Kard.objects.done_in_month(year=year, month=month).count()},
        {'Work in progress': len(cards)},
    ]

    context = {
        'title': "Dashboard",
        'metrics': metrics,
        'cards': cards,
        'updated_at': datetime.datetime.now(),
        'version': __version__,
    }

    return render_template('dashboard.html', **context)
