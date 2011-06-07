import datetime

from flask import (
    render_template,
    make_response,
    request,
    redirect,
    url_for,
    flash,
    abort,
)

from kardboard import app, __version__
from kardboard.models import Kard
from kardboard.forms import NewCardForm, CardForm, _make_choice_field_ready


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


@app.route('/done/')
def done():
    cards = Kard.objects.done()
    cards = sorted(cards, key=lambda c: c.done_date)
    cards.reverse()

    context = {
        'title': "Completed Cards",
        'cards': cards,
        'updated_at': datetime.datetime.now(),
        'version': __version__,
    }

    return render_template('done.html', **context)


@app.route('/done/report/<int:year_number>/<int:month_number>/')
def done_report(year_number, month_number):
    cards = Kard.objects.done_in_month(year_number, month_number)
    cards = sorted(cards, key=lambda c: c.done_date)
    cards.reverse()

    context = {
        'title': "Completed Cards: %s/%s: %s Done" % (month_number,
            year_number, len(cards)),
        'cards': cards,
        'updated_at': datetime.datetime.now(),
        'version': __version__,
    }

    response = make_response(render_template('done-report.txt', **context))
    response.headers['Content-Type'] = "text/plain"
    return response


def _init_card_form(klass, *args, **kwargs):
    f = klass(*args, **kwargs)
    choices = app.config.get('CARD_CATEGORIES')
    if choices:
        f.category.choices = _make_choice_field_ready(choices)
    return f


@app.route('/card/add/', methods=["GET", "POST"])
def card_add():
    f = _init_card_form(NewCardForm, request.form)

    if request.method == "POST" and f.validate():
        card = Kard()
        f.populate_obj(card)
        card.save()
        flash("Card %s successfully added" % card.key)
        return redirect(url_for("card_edit", key=card.key))

    context = {
        'title': "Add a card",
        'form': f,
        'updated_at': datetime.datetime.now(),
        'version': __version__,
    }
    return render_template('card-add.html', **context)


@app.route('/card/edit/<key>/', methods=["GET", "POST"])
def card_edit(key):
    try:
        card = Kard.objects.get(key=key)
    except Kard.DoesNotExist:
        abort(404)

    f = _init_card_form(CardForm, request.form, card)

    if request.method == "POST" and f.validate():
        f.populate_obj(card)
        card.save()
        flash("Card %s successfully edited" % card.key)
        return redirect(url_for("card_edit", key=card.key))

    context = {
        'title': "Edit a card",
        'form': f,
        'updated_at': datetime.datetime.now(),
        'version': __version__,
    }

    return render_template('card-add.html', **context)
