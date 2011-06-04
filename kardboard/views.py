import datetime

from flask import render_template

from kardboard import app, __version__
from kardboard.models import Kard


@app.route('/')
def metaboard():
    cards = Kard.in_progress.all()

    metrics = (
        {'Work in progress': len(cards)},
    )

    context = {
        'title': "Dashboard",
        'metrics': metrics,
        'cards': cards,
        'updated_at': datetime.datetime.now(),
        'version': __version__,
    }

    return render_template('dashboard.html', **context)
