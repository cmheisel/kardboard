import csv
import cStringIO
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
from dateutil.relativedelta import relativedelta

from kardboard import app, __version__
from kardboard.models import Kard
from kardboard.forms import get_card_form, _make_choice_field_ready
from kardboard.util import month_range, slugify, make_end_date
from kardboard.charts import ThroughputChart
from kardboard import tickethelpers


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
        start, end = month_range(date)
        date = end
    if day:
        date = date.replace(day=day)
        scope = 'day'

    date = make_end_date(date=date)

    wip_cards = list(Kard.in_progress(date))
    wip_cards = sorted(wip_cards, key=lambda c: c.current_cycle_time(date))
    wip_cards.reverse()

    backlog_cards = Kard.backlogged(date).order_by('key')

    metrics = [
        {'Ave. Cycle Time': Kard.objects.moving_cycle_time(
            year=date.year, month=date.month, day=date.day)},
        {'Done this week': Kard.objects.done_in_week(
            year=date.year, month=date.month, day=date.day).count()},
        {'Done this month':
            Kard.objects.done_in_month(
                year=date.year, month=date.month).count()},
        {'On the board': len(wip_cards) + backlog_cards.count()},
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
        'wip_cards': wip_cards,
        'backlog_cards': backlog_cards,
        'updated_at': datetime.datetime.now(),
        'version': __version__,
    }

    return render_template('dashboard.html', **context)


@app.route('/state/')
@app.route('/state/<state_slug>/')
def state(state_slug=None):
    states = app.config.get('STATES', [])
    state_mapping = {}
    for state in states:
        state_mapping[slugify(state)] = state

    target_state = None
    if state_slug:
        target_state = state_mapping.get(state_slug, None)
        if not state:
            abort(404)

    if target_state:
        target_states = [target_state, ]
    else:
        target_states = states

    states_data = []
    for state in target_states:
        state_data = {}
        wip_cards = Kard.in_progress().filter(state=state)
        wip_cards = sorted(wip_cards, key=lambda c: c.current_cycle_time())
        wip_cards.reverse()
        state_data['wip_cards'] = wip_cards
        state_data['backlog_cards'] = Kard.backlogged().filter(state=state)
        state_data['title'] = state
        if len(state_data['wip_cards']) > 0 or \
            state_data['backlog_cards'].count() > 0:
            states_data.append(state_data)

    title = "Cards in progress"
    if target_state:
        title = "Cards in %s" % (state, )

    context = {
        'title': title,
        'states_data': states_data,
        'states_count': len(states_data),
        'updated_at': datetime.datetime.now(),
        'version': __version__,
    }
    return render_template('state.html', **context)


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


def _init_new_card_form(*args, **kwargs):
    return _init_card_form(*args, new=True, **kwargs)


def _init_card_form(*args, **kwargs):
    new = kwargs.get('new', False)
    if new:
        del kwargs['new']
    klass = get_card_form(new=new)
    f = klass(*args, **kwargs)
    choices = app.config.get('CARD_CATEGORIES')
    if choices:
        f.category.choices = _make_choice_field_ready(choices)

    states = app.config.get('STATES')
    if states:
        f.state.choices = _make_choice_field_ready(states)
    return f


@app.route('/card/add/', methods=["GET", "POST"])
def card_add():
    f = _init_new_card_form(request.values)

    if request.method == "POST":
        if app.config.get('JIRA_WSDL'):
            if f.key.data and not f.title.data:
                user, passw = app.config.get('JIRA_CREDENTIALS', (None, None))
                j = tickethelpers.JIRAHelper(app, user, passw)
                try:
                    f.title.data = j.get_title(f.key.data)
                except:
                    pass
        if f.validate():
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


@app.route('/card/<key>/edit/', methods=["GET", "POST"])
def card_edit(key):
    try:
        card = Kard.objects.get(key=key)
    except Kard.DoesNotExist:
        abort(404)

    f = _init_card_form(request.form, card)

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


@app.route('/card/<key>/', methods=["GET", "POST"])
def card(key):
    try:
        card = Kard.objects.get(key=key)
    except Kard.DoesNotExist:
        abort(404)

    context = {
        'title': "%s -- %s" % (card.key, card.title),
        'card': card,
        'updated_at': datetime.datetime.now(),
        'version': __version__,
    }
    return render_template('card.html', **context)


@app.route('/card/<key>/delete/', methods=["GET", "POST"])
def card_delete(key):
    try:
        card = Kard.objects.get(key=key)
    except Kard.DoesNotExist:
        abort(404)

    if request.method == "POST" and request.form.get('delete'):
        card.delete()
        return redirect(url_for("dashboard"))
    elif request.method == "POST" and request.form.get('cancel'):
        return redirect(url_for("card", key=card.key))

    context = {
        'title': "%s -- %s" % (card.key, card.title),
        'card': card,
        'updated_at': datetime.datetime.now(),
        'version': __version__,
    }
    return render_template('card-delete.html', **context)


@app.route('/quick/', methods=["GET"])
def quick():
    key = request.args.get('key', None)
    if not key:
        url = url_for('dashboard')
        return redirect(url)

    try:
        card = Kard.objects.get(key=key)
    except Kard.DoesNotExist:
        card = None

    if not card:
        try:
            card = Kard.objects.get(key=key.upper())
        except Kard.DoesNotExist:
            pass

    if card:
        url = url_for('card_edit', key=card.key)
    else:
        url = url_for('card_add', key=key)

    return redirect(url)


@app.route('/card/export/')
def card_export():
    output = cStringIO.StringIO()
    export = csv.DictWriter(output, Kard.EXPORT_FIELDNAMES)
    header_row = [(v, v) for v in Kard.EXPORT_FIELDNAMES]
    export.writerow(dict(header_row))
    for c in Kard.objects.all():
        row = {}
        card = c.to_mongo()
        for name in Kard.EXPORT_FIELDNAMES:
            try:
                value = card[name]
                if hasattr(value, 'second'):
                    value = value.strftime("%m/%d/%Y")
                if hasattr(value, 'strip'):
                    value = value.strip()
                row[name] = value
            except KeyError:
                row[name] = ''
        export.writerow(row)

    response = make_response(output.getvalue())
    content_type = response.headers['Content-Type']
    response.headers['Content-Type'] = \
        content_type.replace('text/html', 'text/plain')
    return response


@app.route('/chart/')
def chart_index():
    context = {
        'title': "Charts",
        'updated_at': datetime.datetime.now(),
        'version': __version__,
    }
    return render_template('charts.html', **context)


@app.route('/chart/throughput/')
@app.route('/chart/throughput/<int:months>/')
def chart_throughput(months=6, start=None):
    start = start or datetime.datetime.today()
    end_start, end_end = month_range(start)
    months_ago = end_start - relativedelta(months=months - 1)

    start_start, start_end = month_range(months_ago)

    month_ranges = [(start_start, start_end), ]

    for i in xrange(0, months - 2):
        next_month = month_ranges[-1][0] + relativedelta(months=1)
        start, end = month_range(date=next_month)
        month_ranges.append((start, end))
    month_ranges.append((end_start, end_end))

    month_counts = []
    for arange in month_ranges:
        start, end = arange
        num = Kard.objects.filter(done_date__gte=start,
            done_date__lte=end).count()
        month_counts.append((start.strftime("%B"), num))

    chart = ThroughputChart(900, 300)
    chart.add_bars(month_counts)

    context = {
        'title': "How much have we done?",
        'updated_at': datetime.datetime.now(),
        'chart': chart,
        'month_counts': month_counts,
        'version': __version__,
    }

    return render_template('chart-throughput.html', **context)
