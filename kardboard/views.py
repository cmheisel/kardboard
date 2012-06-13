import csv
import cStringIO
import datetime
import importlib

from dateutil import relativedelta
from flask import (
    render_template,
    make_response,
    request,
    redirect,
    session,
    url_for,
    flash,
    abort,
)

import kardboard.auth
from kardboard.version import VERSION
from kardboard.app import app, cache
from kardboard.models import Kard, DailyRecord, Q, Person, ReportGroup, States, DisplayBoard, PersonCardSet, FlowReport
from kardboard.forms import get_card_form, _make_choice_field_ready, LoginForm, CardBlockForm, CardUnblockForm
import kardboard.util
from kardboard.util import (
    month_range,
    slugify,
    make_start_date,
    make_end_date,
    month_ranges,
    log_exception,
)
from kardboard.charts import (
    ThroughputChart,
    MovingCycleTimeChart,
    CumulativeFlowChart,
    CycleDistributionChart
)

states = States()


def dashboard(year=None, month=None, day=None):
    date = kardboard.util.now()
    now = kardboard.util.now()
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
                year=date.year, month=date.month, day=date.day).count()},
        {'On the board': len(wip_cards) + backlog_cards.count()},
    ]

    title = "Dashboard"
    if scope == 'year':
        title += " for %s"
    if scope == 'month':
        title += " for %s/%s" % (date.month, date.year)
    if scope == 'day' or scope == 'current':
        title += " for %s/%s/%s" % (date.month, date.day, date.year)

    forward_date = date + relativedelta.relativedelta(days=1)
    back_date = date - relativedelta.relativedelta(days=1)

    if forward_date > now:
        forward_date = None

    context = {
        'forward_date': forward_date,
        'back_date': back_date,
        'scope': scope,
        'date': date,
        'title': title,
        'metrics': metrics,
        'wip_cards': wip_cards,
        'backlog_cards': backlog_cards,
        'updated_at': now,
        'version': VERSION,
    }

    return render_template('dashboard.html', **context)


def team(team_slug=None):
    date = datetime.datetime.now()
    date = make_end_date(date=date)
    teams = app.config.get('CARD_TEAMS', [])

    team_mapping = {}
    for team in teams:
        team_mapping[slugify(team)] = team

    target_team = None
    if team_slug:
        target_team = team_mapping.get(team_slug, None)
        if not team:
            abort(404)

    board = DisplayBoard(teams=[target_team, ])

    metrics = [
        {'Ave. Cycle Time': Kard.objects.filter(team=target_team).moving_cycle_time(
            year=date.year, month=date.month, day=date.day)},
        {'Done this week': Kard.objects.filter(team=target_team).done_in_week(
            year=date.year, month=date.month, day=date.day).count()},
        {'Done this month':
            Kard.objects.filter(team=target_team).done_in_month(
                year=date.year, month=date.month, day=date.day).count()},
        {'On the board': len(board.cards)},
    ]

    done_cards = Kard.objects.done().filter(team=target_team).order_by('-done_date')

    title = "%s cards" % target_team

    context = {
        'title': title,
        'done_cards': done_cards,
        'metrics': metrics,
        'board': board,
        'date': date,
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
    }

    return render_template('state.html', **context)


def state():
    date = datetime.datetime.now()
    date = make_end_date(date=date)

    board = DisplayBoard()  # defaults to all teams, 7 days of done

    title = app.config.get('SITE_NAME')

    wip_cards = Kard.in_progress(date)
    backlog_cards = Kard.backlogged(date)
    metrics = [
        {'Ave. Cycle Time': Kard.objects.moving_cycle_time(
            year=date.year, month=date.month, day=date.day)},
        {'Done this week': Kard.objects.done_in_week(
            year=date.year, month=date.month, day=date.day).count()},
        {'Done this month':
            Kard.objects.done_in_month(
                year=date.year, month=date.month, day=date.day).count()},
        {'On the board': wip_cards.count() + backlog_cards.count()},
    ]

    context = {
        'title': title,
        'board': board,
        'states': states,
        'metrics': metrics,
        'date': date,
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
    }

    return render_template('state.html', **context)


def _init_new_card_form(*args, **kwargs):
    return _init_card_form(*args, new=True, **kwargs)


def _init_card_form(*args, **kwargs):
    new = kwargs.get('new', False)
    if new:
        del kwargs['new']
    klass = get_card_form(new=new)
    f = klass(*args, **kwargs)

    if states:
        f.state.choices = states.for_forms

    teams = app.config.get('CARD_TEAMS')
    if teams:
        f.team.choices = _make_choice_field_ready(teams)

    return f


@kardboard.auth.login_required
def card_add():
    f = _init_new_card_form(request.values)
    card = Kard()
    f.populate_obj(card)

    if request.method == "POST":
        if f.key.data and not f.title.data:
            try:
                f.title.data = card.ticket_system.get_title(key=f.key.data)
            except Exception, e:
                log_exception(e, "Error getting card title via helper")
                pass

        if f.validate():
            # Repopulate now that some data may have come from the ticket
            # helper above
            f.populate_obj(card)
            card.save()
            flash("Card %s successfully added" % card.key)
            return redirect(url_for("card", key=card.key))

    context = {
        'title': "Add a card",
        'form': f,
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
    }
    return render_template('card-add.html', **context)


@kardboard.auth.login_required
@kardboard.util.redirect_to_next_url
def card_edit(key):
    try:
        card = Kard.objects.get(key=key)
    except Kard.DoesNotExist:
        abort(404)

    if request.method == "GET":
        f = _init_card_form(request.form, card)

    if request.method == "POST":
        f = _init_card_form(request.form)
        if f.validate():
            f.populate_obj(card)
            card.save()
            flash("Card %s successfully edited" % card.key)
            return True   # Redirect

    context = {
        'title': "Edit a card",
        'form': f,
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
    }

    return render_template('card-add.html', **context)


@kardboard.auth.login_required
def card(key):
    try:
        card = Kard.objects.get(key=key)
    except Kard.DoesNotExist:
        abort(404)

    context = {
        'title': "%s -- %s" % (card.key, card.title),
        'card': card,
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
    }
    return render_template('card.html', **context)


@kardboard.auth.login_required
@kardboard.util.redirect_to_next_url
def card_delete(key):
    try:
        card = Kard.objects.get(key=key)
    except Kard.DoesNotExist:
        abort(404)

    if request.method == "POST" and request.form.get('delete'):
        card.delete()
        return redirect("/")
    elif request.method == "POST" and request.form.get('cancel'):
        return True  # redirect

    context = {
        'title': "%s -- %s" % (card.key, card.title),
        'card': card,
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
    }
    return render_template('card-delete.html', **context)


@kardboard.auth.login_required
@kardboard.util.redirect_to_next_url
def card_block(key):
    try:
        card = Kard.objects.get(key=key)
        action = 'block'
        if card.blocked:
            action = 'unblock'
    except Kard.DoesNotExist:
        abort(404)

    now = datetime.datetime.now()
    if action == 'block':
        f = CardBlockForm(request.form, blocked_at=now)
    if action == 'unblock':
        f = CardUnblockForm(request.form, unblocked_at=now)

    if 'cancel' in request.form.keys():
        return True  # redirect
    elif request.method == "POST" and f.validate():
        if action == 'block':
            blocked_at = datetime.datetime.combine(
                f.blocked_at.data, datetime.time())
            blocked_at = make_start_date(date=blocked_at)
            result = card.block(f.reason.data, blocked_at)
            if result:
                card.save()
                flash("%s blocked" % card.key)
                return True  # redirect
        if action == 'unblock':
            unblocked_at = datetime.datetime.combine(
                f.unblocked_at.data, datetime.time())
            unblocked_at = make_end_date(date=unblocked_at)
            result = card.unblock(unblocked_at)
            if result:
                card.save()
                flash("%s unblocked" % card.key)
                return True  # redurect

    context = {
        'title': "%s a card" % (action.capitalize(), ),
        'action': action,
        'card': card,
        'form': f,
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
    }

    return render_template('card-block.html', **context)


def quick():
    key = request.args.get('key', None)
    key = key.strip()
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
        url = url_for('card', key=card.key)
    else:
        url = url_for('card_add', key=key)

    return redirect(url)


@kardboard.auth.login_required
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


def reports_index():
    report_conf = app.config.get('REPORT_GROUPS', {})

    report_groups = []
    keys = report_conf.keys()
    keys.sort()

    for key in keys:
        conf = report_conf[key]
        report_groups.append((key, conf[1]))

    context = {
        'title': "Reports",
        'updated_at': datetime.datetime.now(),
        'report_groups': report_groups,
        'all': ('all', "All teams"),
        'version': VERSION,
    }
    return render_template('reports.html', **context)


def done(group="all", months=3, start=None):
    start = start or datetime.datetime.today()
    months_ranges = month_ranges(start, months)

    start = months_ranges[0][0]
    end = months_ranges[-1][-1]

    rg = ReportGroup(group, Kard.objects.done())
    done = rg.queryset

    cards = done.filter(done_date__gte=start,
        done_date__lte=end).order_by('-done_date')

    context = {
        'title': "Completed Cards",
        'cards': cards,
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
    }

    return render_template('done.html', **context)

def report_leaderboard(group="all", months=3, person=None, start_month=None, start_year=None):
    start = datetime.datetime.today()
    if start_month and start_year:
        start = start.replace(month=start_month, year=start_year)
    months_ranges = month_ranges(start, months)

    start = months_ranges[0][0]
    end = months_ranges[-1][-1]

    rg = ReportGroup(group, Kard.objects.done())
    done = rg.queryset

    cards = done.filter(done_date__gte=start,
        done_date__lte=end)

    people = {}
    for card in cards:
        try:
            devs = card.ticket_system_data['developers']
            for d in devs:
                p = people.get(d, PersonCardSet(d))
                p.add_card(card)
                people[d] = p
        except KeyError:
            pass

    if person:
        person = people.get(person, None)
        people = []
        if not person:
            abort(404)
    else:
        people = people.values()
        people.sort(reverse=True)

    context = {
        'people': people,
        'person': person,
        'months': months,
        'group': group,
        'start': start,
        'end': end,
        'start_month': start_month,
        'start_year': start_year,
        'title': "Developer Leaderboard",
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
    }
    if person:
        context['title'] = "%s: %s" % (person.name, context['title'])

    return render_template('leaderboard.html', **context)


def report_service_class(group="all", months=3, start=None):
    start = start or datetime.datetime.today()
    months_ranges = month_ranges(start, months)
    rg = ReportGroup(group, Kard.objects)
    rg_cards = rg.queryset
    classes = rg_cards.distinct('service_class')
    classes.sort()

    datatable = {
        'headers': ('Month', 'Class', 'Throughput', 'Cycle Time', 'Lead Time'),
        'rows': [],
    }

    months = []
    for arange in months_ranges:
        for cls in classes:
            row = []
            start, end = arange
            filtered_cards = Kard.objects.filter(done_date__gte=start,
                done_date__lte=end, _service_class=cls)
            rg = ReportGroup(group, filtered_cards)
            cards = rg.queryset

            if cards.count() == 0:
                # We don't need to have rows for
                # service classes we didn't do
                continue
            month_name = start.strftime("%B")
            if month_name not in months:
                row.append(month_name)
                months.append(month_name)
            else:
                row.append('')
            row.append(cls)
            row.append(cards.count())
            if cards.count() > 0:
                row.append("%d" % cards.average('_cycle_time'))
                row.append("%d" % cards.average('_lead_time'))
            else:
                row.append('N/A')
                row.append('N/A')
            row = tuple(row)
            datatable['rows'].append(row)

    context = {
        'title': "By service class",
        'updated_at': datetime.datetime.now(),
        'datatable': datatable,
        'version': VERSION,
    }

    return render_template('report-classes.html', **context)


def chart_throughput(group="all", months=3, start=None):
    start = start or datetime.datetime.today()
    months_ranges = month_ranges(start, months)

    month_counts = []
    for arange in months_ranges:
        start, end = arange
        filtered_cards = Kard.objects.filter(done_date__gte=start,
            done_date__lte=end)
        rg = ReportGroup(group, filtered_cards)
        cards = rg.queryset

        num = cards.count()
        month_counts.append((start.strftime("%B"), num))

    chart = ThroughputChart(900, 300)
    chart.add_bars(month_counts)

    context = {
        'title': "How much have we done?",
        'updated_at': datetime.datetime.now(),
        'chart': chart,
        'month_counts': month_counts,
        'version': VERSION,
    }

    return render_template('chart-throughput.html', **context)


def chart_cycle(group="all", months=3, year=None, month=None, day=None):
    today = datetime.datetime.today()
    if day:
        end_day = datetime.datetime(year=year, month=month, day=day)
        if end_day > today:
            end_day = today
    else:
        end_day = today

    start_day = end_day - relativedelta.relativedelta(months=months)
    start_day = make_start_date(date=start_day)
    end_day = make_end_date(date=end_day)

    records = DailyRecord.objects.filter(
        date__gte=start_day,
        date__lte=end_day,
        group=group)

    daily_moving_averages = [(r.date, r.moving_cycle_time) for r in records]
    daily_moving_lead = [(r.date, r.moving_lead_time) for r in records]

    chart = MovingCycleTimeChart(900, 300)
    chart.add_first_line(daily_moving_lead)
    chart.add_line(daily_moving_averages)
    chart.set_legend(('Lead time', 'Cycle time'))

    daily_moving_averages.reverse()  # reverse order for display
    daily_moving_lead.reverse()
    context = {
        'title': "How quick can we do it?",
        'updated_at': datetime.datetime.now(),
        'chart': chart,
        'daily_averages': daily_moving_averages,
        'daily_lead': daily_moving_lead,
        'version': VERSION,
    }

    return render_template('chart-cycle.html', **context)


def chart_cycle_distribution(group="all", months=3):
    ranges = (
        (0, 4, "< 5 days"),
        (5, 10, "5-10 days"),
        (11, 15, "11-15 days"),
        (16, 20, "16-20 days"),
        (21, 25, "21-25 days"),
        (26, 30, "26-30 days",),
        (31, 9999, "> 30 days"),
    )
    today = datetime.datetime.today()
    start_day = today - relativedelta.relativedelta(months=months)
    start_day = make_start_date(date=start_day)
    end_day = make_end_date(date=today)

    context = {
        'title': "How quick can we do it?",
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
    }

    query = Q(done_date__gte=start_day) & Q(done_date__lte=end_day)
    rg = ReportGroup(group, Kard.objects.filter(query))

    total = rg.queryset.count()
    if total == 0:
        context = {
            'error': "Zero cards were completed in the past %s months" % months
        }
        return render_template('chart-cycle-distro.html', **context)

    distro = []
    for row in ranges:
        lower, upper, label = row
        query = Q(done_date__gte=start_day) & Q(done_date__lte=end_day) & \
            Q(_cycle_time__gte=lower) & Q(_cycle_time__lte=upper)
        pct = ReportGroup(group, Kard.objects.filter(query)).queryset.count() / float(total)
        distro.append((label, pct))

    chart = CycleDistributionChart(700, 400)
    chart.add_data([r[1] for r in distro])
    chart.set_pie_labels([r[0] for r in distro])
    context = {
        'data': distro,
        'chart': chart,
        'title': "How quick can we do it?",
        'updated_at': datetime.datetime.now(),
        'distro': distro,
        'version': VERSION,
    }
    return render_template('chart-cycle-distro.html', **context)


def robots():
    response = make_response(render_template('robots.txt'))
    content_type = response.headers['Content-type']
    content_type.replace('text/html', 'text/plain')
    return response


def report_flow(group="all", months=3):
    end = kardboard.util.now()
    months_ranges = month_ranges(end, months)

    start_day = make_start_date(date=months_ranges[0][0])
    end_day = make_end_date(date=end)

    records = DailyRecord.objects.filter(
        date__gte=start_day,
        date__lte=end_day,
        group=group)

    chart = CumulativeFlowChart(900, 300)
    chart.add_data([r.backlog_cum for r in records])
    chart.add_data([r.in_progress_cum for r in records])
    chart.add_data([r.done for r in records])
    chart.setup_grid(records)

    records.order_by('-date')
    context = {
        'title': "Cumulative Flow",
        'updated_at': datetime.datetime.now(),
        'chart': chart,
        'flowdata': records,
        'version': VERSION,
    }

    return render_template('chart-flow.html', **context)

def _detailed_flow_chart(reports):
    chart = {}
    chart['categories'] = [report.date.strftime("%m/%d") for report in reports]

    # TODO: This is a really slow operation, 8 seconds on my laptop for 5 days with 8 states/day
    # For now tasks.update_flow_reports not only captures the data for the day, but it also
    # calls cache.delete_memoize for the most likely combinations of groups and months
    # and then calls report_detailed_flow again to re-prime the cache.
    series = []
    for state in States():
        seri = {'name': state}
        data = [report.snapshot.get(state, {}).get('count', 0) for report in reports]
        seri['data'] = data
        series.append(seri)
    chart['series'] = series

    import json
    for key, value in chart.items():
        chart[key] = json.dumps(value)

    return chart

def report_detailed_flow(group="all", months=3):
    end = kardboard.util.now()
    months_ranges = month_ranges(end, months)

    start_day = make_start_date(date=months_ranges[0][0])
    end_day = make_end_date(date=end)

    reports = FlowReport.objects.filter(
        date__gte=start_day,
        date__lte=end_day,
        group=group)
    if not reports:
        abort(404)

    cache_key = 'cumflowchart-%s-%s' % (group, months)
    chart = cache.get(cache_key)
    if not chart:
        chart = _detailed_flow_chart(reports)
        # FlowReport objects are only refreshed every 5 minutes by default but there is
        # a job, see details below, that deletes and refreshes this
        # from cache. So we set a long expiry.
        cache.set(cache_key, chart, 24 * 60 * 60)

    reports.order_by('-date')
    context = {
        'title': "Detailed Cumulative Flow",
        'reports': reports,
        'months': months,
        'chart': chart,
        'updated_at': reports[0].updated_at,
        'states': States(),
        'version': VERSION,
    }
    return render_template('report-detailed-flow.html', **context)

@kardboard.util.redirect_to_next_url
def login():
    f = LoginForm(request.form)

    if request.method == "POST" and f.validate():
        helper_setting = app.config['TICKET_HELPER']
        modname = '.'.join(helper_setting.split('.')[:-1])
        klassnam = helper_setting.split('.')[-1]
        mod = importlib.import_module(modname)
        klass = getattr(mod, klassnam)

        helper = klass(app.config, None)
        result = helper.login(f.username.data, f.password.data)
        if result:
            session['username'] = f.username.data
            return True  # redirect
        else:
            f.errors['auth_failure'] = 'Username/password incorrect'


    context = {
        'title': "Login",
        'form': f,
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
    }
    return render_template('login.html', **context)


def logout():
    if 'username' in session:
        del session['username']
    next_url = request.args.get('next') or '/'
    return redirect(next_url)


def person(name):
    try:
        person = Person.objects.get(name=name)
    except Person.DoesNotExist:
        abort(404)

    context = {
        'title': "%s's information" % person.name,
        'person': person,
        'in_progress_reported': person.in_progress(person.reported),
        'in_progress_developed': person.in_progress(person.developed),
        'in_progres_tested': person.in_progress(person.tested),
        'reported': person.is_done(person.reported),
        'developed': person.is_done(person.developed),
        'tested': person.is_done(person.tested),
        'updated_at': person.updated_at,
        'version': VERSION,
    }
    return render_template('person.html', **context)
