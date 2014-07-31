import csv
import cStringIO
import datetime
import importlib
import os
import time
from math import isnan

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
    send_from_directory,
    jsonify,
)

import kardboard.auth
from kardboard.version import VERSION
from kardboard.app import app
from kardboard.models import Kard, DailyRecord, Q, Person, ReportGroup, States, DisplayBoard, PersonCardSet, FlowReport, StateLog, ServiceClassRecord, ServiceClassSnapshot
from kardboard.forms import get_card_form, _make_choice_field_ready, LoginForm, CardBlockForm, CardUnblockForm
import kardboard.util
from kardboard.services import teams as teams_service
from kardboard.services.funnel import Funnel
from kardboard.services.wiplimits import WIPLimits
from kardboard.util import (
    munge_date,
    month_range,
    make_start_date,
    make_end_date,
    month_ranges,
    log_exception,
    now,
    week_range,
)


def _get_date():
    date = datetime.datetime.now()
    date = make_end_date(date=date)
    return date


def _get_teams():
    teams = teams_service.setup_teams(
        app.config
    )
    return teams


def _find_team_by_slug(team_slug, teams):
    team_mapping = teams.slug_name_mapping
    target_team = team_mapping.get(team_slug, None)
    team = teams.find_by_name(target_team)
    return team


def _get_excluded_classes():
    service_class_conf = app.config.get('SERVICE_CLASSES', {})
    exclude_classes = []
    for sclass, sclass_data in service_class_conf.items():
        if sclass_data.get('unplanned', False):
            exclude_classes.append(sclass)
    return exclude_classes


def _make_backlog_markers(lead_time, weekly_throughput, backlog_cards):
    backlog_markers = []
    if lead_time is None or isnan(lead_time) or weekly_throughput <= 0:
        return backlog_markers

    counter = 0
    batch_counter = 0
    for k in backlog_cards:
        if counter % weekly_throughput == 0:
            batch_counter += 1
            est_done_date = datetime.datetime.now() + relativedelta.relativedelta(days=lead_time * batch_counter)
            start_date, end_date = week_range(est_done_date)
            est_done_monday = end_date + relativedelta.relativedelta(days=2)  # Adjust to Monday
            backlog_markers.append(est_done_monday)
        counter += 1
    return backlog_markers


def _team_backlog_markers(team, cards, weeks=12):
    exclude_classes = _get_excluded_classes()

    team_stats = teams_service.TeamStats(team.name, exclude_classes)

    weekly_throughput = team_stats.weekly_throughput_ave(weeks)
    confidence_80 = team_stats.percentile(.80, weeks)
    metrics_cards = team_stats.card_info
    metrics_cards = sorted(metrics_cards, key=lambda c: c['cycle_time'])
    metrics_cards.reverse()

    metrics_histogram = team_stats.histogram(weeks)
    metrics_histogram_keys = metrics_histogram.keys()
    metrics_histogram_keys.sort()
    average = team_stats.average(weeks)
    median = team_stats.median(weeks)

    backlog_marker_data = {
        'weeks': weeks,
        'exclude_classes': exclude_classes,
        'histogram': metrics_histogram,
        'histogram_keys': metrics_histogram_keys,
        'cards': metrics_cards,
        'weekly_throughput': weekly_throughput,
        'average': average,
        'median': median,
        'confidence_80': confidence_80,
        'standard_deviation': team_stats.standard_deviation(weeks),
    }

    backlog_markers = _make_backlog_markers(
        confidence_80,
        weekly_throughput,
        cards,
    )

    return backlog_marker_data, backlog_markers


def zero_if_none(value):
    if value is None:
        return 0
    return value


def team(team_slug=None):
    from kardboard.services.boards import TeamBoard

    teams = _get_teams()
    team = _find_team_by_slug(team_slug, teams)

    try:
        wip_limit_config = app.config['WIP_LIMITS'][team_slug]
    except KeyError:
        wip_limit_config = {}

    conwip = wip_limit_config.get('conwip', None)
    wip_limits = WIPLimits(
        name=team_slug,
        conwip=conwip,
        columns=wip_limit_config,
    )

    weeks = 4
    exclude_classes = _get_excluded_classes()
    team_stats = teams_service.TeamStats(team.name, exclude_classes)
    weekly_throughput = team_stats.weekly_throughput_ave(weeks)

    hit_sla = team_stats.hit_sla(weeks)
    hit_sla_delta = team_stats.hit_sla(weeks, weeks_offset=weeks)
    hit_sla, hit_sla_delta = zero_if_none(hit_sla), zero_if_none(hit_sla_delta)
    hit_sla_delta = hit_sla - hit_sla_delta

    total_throughput = teams_service.TeamStats(team.name).throughput(weeks)
    total_throughput_delta = teams_service.TeamStats(team.name).throughput(weeks,
        weeks_offset=weeks)
    total_throughput, total_throughput_delta = zero_if_none(total_throughput), zero_if_none(total_throughput_delta)
    total_throughput_delta = total_throughput - total_throughput_delta

    cycle_time = team_stats.percentile(.8, weeks)
    cycle_time_delta = team_stats.percentile(.8, weeks, weeks_offset=weeks)
    cycle_time, cycle_time_delta = zero_if_none(cycle_time), zero_if_none(cycle_time_delta)
    cycle_time_delta = cycle_time - cycle_time_delta

    metrics = [
        {
            'name': 'Throughput',
            'value': total_throughput,
            'delta': total_throughput_delta,
        },
        {
            'name': 'Hit SLA',
            'value': hit_sla,
            'delta': hit_sla_delta,
        },
        {
            'name': 'Cycle time',
            'value': cycle_time,
            'delta': cycle_time_delta,
        },
    ]

    board = TeamBoard(team.name, States(), wip_limits)
    backlog_limit = weekly_throughput * 4 or 30
    cards = Kard.objects.for_team_board(
        team=team.name,
        backlog_limit=backlog_limit,
        done_days=7,
    )
    board.add_cards(cards)

    backlog_marker_data, backlog_markers = _team_backlog_markers(
        team,
        board.columns[0]['cards'],
        weeks,
    )

    report_config = (
        {'slug': 'assignee', 'name': "Assignee"},
        {'slug': 'cycle/distribution/all', 'name': "Cycle time", 'months': 1},
        {'slug': 'service-class', 'name': 'Service class'},
        {'slug': 'blocked', 'name': 'Blocked', 'months': 3},
        {'slug': 'done', 'name': 'Done', 'months': 1},
        {'slug': 'leaderboard', 'name': 'Leaderboard', 'months': 3},
        {'slug': 'flow/detail', 'name': "Cumulative Flow", 'months': 2},
    )

    context = {
        'title': "%s cards" % team.name,
        'metrics': metrics,
        'wip_limits': wip_limits,
        'team': team,
        'teams': teams,
        'board': board,
        'round': round,
        'backlog_markers': backlog_markers,
        'backlog_marker_data': backlog_marker_data,
        'weekly_throughput': weekly_throughput,
        'report_config': report_config,
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
        'authenticated': kardboard.auth.is_authenticated(),
    }

    return render_template('team.html', **context)


def team_backlog(team_slug=None):
    if request.method == "POST":
        if kardboard.auth.is_authenticated() is False:
            abort(403)

        start = time.time()
        card_key_list = request.form.getlist('card[]')
        counter = 1
        for card_key in card_key_list:
            Kard.objects(
                key=card_key.strip()
            ).only('priority').update_one(set__priority=counter)
            counter += 1

        elapsed = (time.time() - start)
        return jsonify(message="Reordered %s cards in %.2fs" % (counter, elapsed))

    teams = _get_teams()
    team = _find_team_by_slug(team_slug, teams)
    weeks = 4

    backlog = Kard.objects.filter(
        team=team.name,
        state=States().backlog,
    ).exclude('_ticket_system_data').order_by('priority')

    backlog_marker_data, backlog_markers = _team_backlog_markers(team, backlog, weeks)

    backlog_without_order = [k for k in backlog if k.priority is None]
    backlog_with_order = [k for k in backlog if k.priority is not None]
    backlog_with_order.sort(key=lambda k: k.priority)
    backlog = backlog_with_order + backlog_without_order

    title = "%s" % team.name

    context = {
        'title': title,
        'team_slug': team_slug,
        'team': team,
        'backlog': backlog,
        'backlog_markers': backlog_markers,
        'backlog_marker_data': backlog_marker_data,
        'updated_at': datetime.datetime.now(),
        'teams': teams,
        'version': VERSION,
        'authenticated': kardboard.auth.is_authenticated(),
    }

    return render_template('team-backlog.html', **context)


def funnel(state_slug):
    states = States()
    try:
        state = states.find_by_slug(state_slug)
        funnel = Funnel(state, app.config.get('FUNNEL_VIEWS', {})[state])
    except KeyError:
        abort(404)

    cards = funnel.ordered_cards()

    funnel_auth = False
    if kardboard.auth.is_authenticated() is True:
        funnel_auth = funnel.is_authorized(session.get('username', ''))

    if request.method == "POST":
        if kardboard.auth.is_authenticated() is False or funnel_auth is False:
            abort(403)

        start = time.time()
        card_key_list = request.form.getlist('card[]')

        counter = 1
        for card_key in card_key_list:
            Kard.objects(
                key=card_key.strip()
            ).only('priority').update_one(set__priority=counter)
            counter += 1

        elapsed = (time.time() - start)
        return jsonify(message="Reordered %s cards in %.2fs" % (counter, elapsed))

    title = "%s: All boards" % state

    funnel_markers = funnel.markers()

    context = {
        'title': title.replace("Backlog", "Ready: Elabo").replace("OTIS", "TIE"),
        'state': state,
        'state_slug': state_slug,
        'cards': cards,
        'times_in_state': funnel.times_in_state(),
        'funnel_throughput': funnel.throughput,
        'funnel_markers': funnel_markers,
        'funnel_auth': funnel_auth,
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
        'authenticated': kardboard.auth.is_authenticated(),
    }

    return render_template('funnel.html', **context)


def state():
    title = app.config.get('SITE_NAME')

    teams = teams_service.setup_teams(
        app.config
    )

    context = {
        'title': title,
        'teams': teams,
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
    }
    return render_template('state.html', **context)


def _init_new_card_form(*args, **kwargs):
    return _init_card_form(*args, new=True, **kwargs)


def _init_card_form(*args, **kwargs):
    states = States()
    new = kwargs.get('new', False)
    if new:
        del kwargs['new']
    klass = get_card_form(new=new)
    f = klass(*args, **kwargs)

    if states:
        f.state.choices = states.for_forms

    teams = teams_service.setup_teams(
        app.config
    )
    if teams:
        f.team.choices = _make_choice_field_ready(teams.names)

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

    card_log = StateLog.objects.filter(card=card)

    context = {
        'title': "%s -- %s" % (card.key, card.title),
        'card': card,
        'card_log': card_log,
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

    if action == 'block':
        f = CardBlockForm(request.form, blocked_at=now())
    if action == 'unblock':
        f = CardUnblockForm(request.form, unblocked_at=now())

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
        previous = request.args.get('return_path', None)
        if previous:
            return redirect(previous)
        else:
            return redirect('/')

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
    with_defects = app.config.get('DEFECT_TYPES', False)

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
        'with_defects': with_defects,
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


def blocked(group="all", months=3, start=None):
    start = start or datetime.datetime.today()
    months_ranges = month_ranges(start, months)

    start = months_ranges[0][0]
    end = months_ranges[-1][-1]

    rg = ReportGroup(group, Kard.objects())
    blocked_cards = rg.queryset

    blocked_cards = blocked_cards.filter(start_date__gte=start,
        start_date__lte=end, blocked_ever=True).order_by('-start_date')

    context = {
        'title': "Blocked",
        'cards': blocked_cards,
        'start': start,
        'end': end,
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
    }

    return render_template('blocked.html', **context)


def value_txt_report(year_number, month_number, group="all"):
    start_date = munge_date(year=year_number, month=month_number, day=1)
    start_date = make_start_date(date=start_date)

    start_date, end_date = month_range(start_date)

    rg = ReportGroup(group, Kard.objects.done())
    done = rg.queryset

    cards = done.filter(done_date__gte=start_date,
        done_date__lte=end_date).order_by('-done_date')

    cards = [c for c in cards if c.is_card]

    context = {
        'title': "Completed Value Cards",
        'cards': cards,
        'start_date': start_date,
        'end_date': end_date,
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
    }

    response = make_response(render_template('done-report.txt', **context))
    response.headers['Content-Type'] = "text/plain"
    return response


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


def report_service_class(group="all", months=None):
    from kardboard.app import app
    service_class_order = app.config.get('SERVICE_CLASSES', {}).keys()
    service_class_order.sort()
    service_classes = [
        app.config['SERVICE_CLASSES'][k] for k in service_class_order
    ]

    if months is None:
        # We want the current report
        try:
            scr = ServiceClassSnapshot.objects.get(
                group=group,
            )
        except ServiceClassSnapshot.DoesNotExist:
            scr = ServiceClassSnapshot.calculate(
                group=group,
            )
        time_range = 'current'
        start_date = make_start_date(date=datetime.datetime.now())
        end_date = make_end_date(date=datetime.datetime.now())
    else:
        start = now()
        months_ranges = month_ranges(start, months)
        start_date = months_ranges[0][0]
        end_date = months_ranges[-1][1]
        try:
            scr = ServiceClassRecord.objects.get(
                group=group,
                start_date=start_date,
                end_date=end_date,
            )
        except ServiceClassRecord.DoesNotExist:
            scr = ServiceClassRecord.calculate(
                group=group,
                start_date=start_date,
                end_date=end_date,
            )
        time_range = 'past %s months' % months

    context = {
        'title': "Service classes: %s" % time_range,
        'service_classes': service_classes,
        'data': scr.data,
        'start_date': start_date,
        'end_date': end_date,
        'updated_at': scr.updated_at,
        'version': VERSION,
    }

    return render_template('report-service-class.html', **context)


def report_throughput(group="all", months=3, start=None):
    start = start or datetime.datetime.today()
    months_ranges = month_ranges(start, months)
    defect_types = app.config.get('DEFECT_TYPES', None)
    with_defects = defect_types is not None

    month_counts = []
    for arange in months_ranges:
        start, end = arange
        filtered_cards = Kard.objects.filter(done_date__gte=start,
            done_date__lte=end)
        rg = ReportGroup(group, filtered_cards)
        cards = rg.queryset

        if with_defects:
            counts = {'card': 0, 'defect': 0}
            for card in cards:
                if card.type.strip() in defect_types:
                    counts['defect'] += 1
                else:
                    counts['card'] += 1
            month_counts.append((start.strftime("%B '%y"), counts))
        else:
            num = cards.count()
            month_counts.append((start.strftime("%B, '%y"), num))

    chart = {}
    chart['categories'] = [c[0] for c in month_counts]

    if with_defects:
        chart['series'] = [
            {
                'data': [c[1]['card'] for c in month_counts],
                'name': 'Cards'
            },
            {
                'data': [c[1]['defect'] for c in month_counts],
                'name': 'Defects'
            }
        ]
    else:
        chart['series'] = [{
            'data': [c[1] for c in month_counts],
            'name': 'Cards',
        }]

    context = {
        'title': "How much have we done?",
        'updated_at': datetime.datetime.now(),
        'chart': chart,
        'month_counts': month_counts,
        'version': VERSION,
        'with_defects': with_defects,
    }

    return render_template('report-throughput.html', **context)


def report_cycle(group="all", months=3, year=None, month=None, day=None):
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
    daily_mad = [(r.date, r.moving_median_abs_dev) for r in records]

    start_date = daily_moving_averages[0][0]
    chart = {}
    chart['series'] = [
        {
            'name': 'Cycle time',
            'data': [r[1] for r in daily_moving_averages],
        },
        {
            'name': 'Unpredictability',
            'data': [r[1] for r in daily_mad],
        }
    ]
    chart['goal'] = app.config.get('CYCLE_TIME_GOAL', ())

    daily_moving_averages.reverse()  # reverse order for display
    daily_moving_lead.reverse()
    daily_mad.reverse()
    context = {
        'title': "How quick can we do it?",
        'updated_at': datetime.datetime.now(),
        'chart': chart,
        'months': months,
        'start_date': start_date,
        'daily_averages': daily_moving_averages,
        'daily_mad': daily_mad,
        'version': VERSION,
    }

    return render_template('report-cycle.html', **context)


def report_assignee(group="all"):
    states = States()
    states_of_interest = [s for s in states if s not in (states.backlog, states.done)]
    # ReportGroup of WIP
    rg = ReportGroup(group, Kard.objects.filter(state__in=states_of_interest))

    distro = {}
    for k in rg.queryset.all():
        assignee = k._assignee or "Unassigned"
        distro.setdefault(assignee, 0)
        distro[assignee] += 1

    total = 0
    total = float(sum(distro.values()))

    distro = distro.items()
    distro.sort(key=lambda x: x[1])
    distro.reverse()

    percentages = [(x[0], (x[1] / total)) for x in distro]
    percentages = [(x[0], round(x[1], 2)) for x in percentages]

    chart = {}
    chart['data'] = percentages

    context = {
        'data': distro,
        'chart': chart,
        'total': total,
        'title': "Assignee breakdown",
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
    }
    return render_template('report-assignee.html', **context)


def report_defect_cycle_distribution(group="all", months=3):
    return report_cycle_distribution(group, months, limit='defects')


def report_card_cycle_distribution(group="all", months=3):
    return report_cycle_distribution(group, months, limit='cards')


def report_cycle_distribution(group="all", months=3, limit=None):
    from kardboard.services.reports import CycleTimeDistribution

    defects_only, cards_only = False, False
    if limit == 'cards':
        cards_only = True
    if limit == 'defects':
        defects_only = True

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
    if defects_only:
        query = query & Q(_type__in=app.config.get('DEFECT_TYPES', []))
    elif cards_only:
        query = query & Q(_type__nin=app.config.get('DEFECT_TYPES', []))
    rg = ReportGroup(group, Kard.objects.filter(query))

    cards = list(rg.queryset)

    total = len(cards)
    if total == 0:
        context = {
            'error': "Zero cards were completed in the past %s months" % months,
        }
        return render_template('report-cycle-distro.html', **context)

    cdr = CycleTimeDistribution(cards=cards)

    chart = {}
    chart['categories'] = cdr.days()
    chart['series'] = []

    service_class_series = cdr.service_class_series()
    sclasses = service_class_series.keys()
    sclasses.sort()

    for sclass in sclasses:
        seri = service_class_series[sclass]
        chart['series'].append(
            dict(name=sclass, data=seri)
        )

    context = {
        'histogram_data': cdr.histogram(),
        'chart': chart,
        'title': "How quick can we do it?",
        'months': months,
        'total': total,
        'updated_at': datetime.datetime.now(),
        'version': VERSION,
    }
    if defects_only:
        context['title'] = "Defects: %s" % (context['title'])
        context['card_type'] = 'defects'
    elif cards_only:
        context['title'] = "Cards: %s" % (context['title'])
        context['card_type'] = 'cards'
    else:
        context['title'] = "All: %s" % (context['title'])
        context['card_type'] = 'cards and defects'

    return render_template('report-cycle-distro.html', **context)


def robots():
    response = make_response(render_template('robots.txt'))
    content_type = response.headers['Content-type']
    content_type.replace('text/html', 'text/plain')
    return response


def report_efficiency(group="all", months=3):
    state_mappings = app.config.get('EFFICIENCY_MAPPINGS', None)
    if state_mappings is None:
        abort(404)
    stats = teams_service.EfficiencyStats(mapping=state_mappings)

    end = kardboard.util.now()
    months_ranges = month_ranges(end, months)

    start_day = make_start_date(date=months_ranges[0][0])
    end_day = make_end_date(date=end)

    records = FlowReport.objects.filter(
        date__gte=start_day,
        date__lte=end_day,
        group=group
    )

    incremented_state_counts = []
    for r in records:
        a_record = {'date': r.date}
        a_record.update(r.state_counts)
        incremented_state_counts.append(a_record)

    for group_name in app.config.get('EFFICIENCY_INCREMENTS', ()):
        stats.make_incremental(incremented_state_counts, group_name)

    data = []
    for r in incremented_state_counts:
        efficiency_stats = stats.calculate(r)
        data.append(
            {'date': r['date'], 'stats': efficiency_stats}
        )

    chart = {}
    chart['categories'] = [report.date.strftime("%m/%d") for report in records]
    group_names = app.config.get('EFFICIENCY_MAPPINGS_ORDER', state_mappings.keys())
    series = []
    for group_name in group_names:
        seri_data = []
        for d in data:
            seri_data.append(d['stats'][group_name])
        seri = dict(name=group_name, data=seri_data)
        series.append(seri)
    chart['series'] = series

    table_data = []
    for row in data:
        table_row = {'Date': row['date']}
        for group_name in group_names:
            table_row[group_name] = row['stats'][group_name]
        table_data.append(table_row)

    start_date = records.order_by('date').first().date
    context = {
        'title': "Efficiency",
        'start_date': start_date,
        'chart': chart,
        'table_data': table_data,
        'data_keys': ['Date', ] + list(group_names),
        'updated_at': records.order_by('date')[len(records) - 1].date,
        'version': VERSION,
    }
    return render_template('chart-efficiency.html', **context)


def report_flow(group="all", months=3):
    end = kardboard.util.now()
    months_ranges = month_ranges(end, months)

    start_day = make_start_date(date=months_ranges[0][0])
    end_day = make_end_date(date=end)

    records = DailyRecord.objects.filter(
        date__gte=start_day,
        date__lte=end_day,
        group=group)

    chart = {}
    chart['categories'] = [report.date.strftime("%m/%d") for report in records]
    series = [
        {'name': "Planning", 'data': []},
        {'name': "Todo", 'data': []},
        {'name': "Done", 'data': []},
    ]
    for row in records:
        series[0]['data'].append(row.backlog)
        series[1]['data'].append(row.in_progress)
        series[2]['data'].append(row.done)
    chart['series'] = series

    start_date = records.order_by('date').first().date
    records.order_by('-date')
    context = {
        'title': "Cumulative Flow",
        'updated_at': datetime.datetime.now(),
        'chart': chart,
        'start_date': start_date,
        'flowdata': records,
        'version': VERSION,
    }
    return render_template('chart-flow.html', **context)


def report_detailed_flow_cards(group="all", months=3):
    return report_detailed_flow(group, months, cards_only=True)


def report_detailed_flow(group="all", months=3, cards_only=False):
    end = kardboard.util.now()
    months_ranges = month_ranges(end, months)

    start_day = make_start_date(date=months_ranges[0][0])
    end_day = make_end_date(date=end)

    if cards_only:
        only_arg = ('state_card_counts', 'date', 'group')
    else:
        only_arg = ('state_counts', 'date', 'group')

    reports = FlowReport.objects.filter(
        date__gte=start_day,
        date__lte=end_day,
        group=group).only(*only_arg)
    if not reports:
        abort(404)

    chart = {}
    chart['categories'] = []

    series = []
    for state in States():
        seri = {'name': state, 'data': []}
        series.append(seri)

    done_starting_point = 0
    for report in reports:
        chart['categories'].append(report.date.strftime("%m/%d"))
        for seri in series:
            if cards_only:
                daily_seri_data = report.state_card_counts.get(seri['name'], 0)
            else:
                daily_seri_data = report.state_counts.get(seri['name'], 0)

            if seri['name'] == "Done":
                if len(seri['data']) == 0:
                    done_starting_point = daily_seri_data
                    daily_seri_data = 0
                else:
                    daily_seri_data = daily_seri_data - done_starting_point

            seri['data'].append(daily_seri_data)
    chart['series'] = series

    start_date = reports.order_by('date').first().date
    reports.order_by('-date')
    context = {
        'title': "Detailed Cumulative Flow",
        'reports': reports,
        'months': months,
        'cards_only': cards_only,
        'chart': chart,
        'start_date': start_date,
        'updated_at': reports[0].updated_at,
        'states': States(),
        'version': VERSION,
    }
    return render_template('report-detailed-flow.html', **context)


@kardboard.util.redirect_to_next_url
def login():
    if session.get('username', None) is not None:
        return True

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


def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


app.add_url_rule('/', 'state', state)
app.add_url_rule('/card/<key>/', 'card', card, methods=["GET", "POST"])
app.add_url_rule('/card/add/', 'card_add', card_add, methods=["GET", "POST"])
app.add_url_rule('/card/<key>/edit/', 'card_edit', card_edit, methods=["GET", "POST"])
app.add_url_rule('/card/<key>/delete/', 'card_delete', card_delete, methods=["GET", "POST"])
app.add_url_rule('/card/<key>/block/', 'card_block', card_block, methods=["GET", "POST"])
app.add_url_rule('/card/export/', 'card_export', card_export)
app.add_url_rule('/reports/', 'reports_index', reports_index)
app.add_url_rule('/reports/<group>/throughput/', 'report_throughput', report_throughput)
app.add_url_rule('/reports/<group>/throughput/<int:months>/', 'report_throughput', report_throughput)
app.add_url_rule('/reports/<group>/cycle/', 'report_cycle', report_cycle)
app.add_url_rule('/reports/<group>/cycle/<int:months>/', 'report_cycle', report_cycle)
app.add_url_rule('/reports/<group>/cycle/from/<int:year>/<int:month>/<int:day>/', 'report_cycle', report_cycle)
app.add_url_rule('/reports/<group>/cycle/distribution/', 'report_card_cycle_distribution', report_card_cycle_distribution)
app.add_url_rule('/reports/<group>/cycle/distribution/<int:months>/', 'report_card_cycle_distribution', report_card_cycle_distribution)
app.add_url_rule('/reports/<group>/cycle/distribution/defects/', 'report_defect_cycle_distribution', report_defect_cycle_distribution)
app.add_url_rule('/reports/<group>/cycle/distribution/defects/<int:months>/', 'report_defect_cycle_distribution', report_defect_cycle_distribution)
app.add_url_rule('/reports/<group>/cycle/distribution/all/', 'report_cycle_distribution', report_cycle_distribution)
app.add_url_rule('/reports/<group>/cycle/distribution/all/<int:months>/', 'report_cycle_distribution', report_cycle_distribution)
app.add_url_rule('/reports/<group>/flow/', 'report_flow', report_flow)
app.add_url_rule('/reports/<group>/flow/<int:months>/', 'report_flow', report_flow)
app.add_url_rule('/reports/<group>/flow/detail/', 'report_detailed_flow', report_detailed_flow)
app.add_url_rule('/reports/<group>/flow/detail/<int:months>/', 'report_detailed_flow', report_detailed_flow)
app.add_url_rule('/reports/<group>/flow/detail/cards/', 'report_detailed_flow_cards', report_detailed_flow_cards)
app.add_url_rule('/reports/<group>/flow/detail/cards/<int:months>/', 'report_detailed_flow_cards', report_detailed_flow_cards)
app.add_url_rule('/reports/<group>/efficiency/', 'report_efficiency', report_efficiency)
app.add_url_rule('/reports/<group>/efficiency/<int:months>/', 'report_efficiency', report_efficiency)
app.add_url_rule('/reports/<group>/done/', 'done', done)
app.add_url_rule('/reports/<group>/done/<int:months>/', 'done', done)
app.add_url_rule('/reports/<group>/blocked/', 'blocked', blocked)
app.add_url_rule('/reports/<group>/blocked/<int:months>/', 'blocked', blocked)
app.add_url_rule('/reports/<group>/value/<int:year_number>/<int:month_number>/', 'value', value_txt_report)
app.add_url_rule('/reports/<group>/service-class/', 'report_service_class', report_service_class)
app.add_url_rule('/reports/<group>/service-class/<int:months>/', 'report_service_class', report_service_class)
app.add_url_rule('/reports/<group>/assignee/', 'report_assignee', report_assignee)
app.add_url_rule('/reports/<group>/leaderboard/', 'report_leaderboard', report_leaderboard)
app.add_url_rule('/reports/<group>/leaderboard/<int:months>/', 'report_leaderboard', report_leaderboard)
app.add_url_rule('/reports/<group>/leaderboard/<int:start_year>-<int:start_month>/<int:months>/', 'report_leaderboard', report_leaderboard)
app.add_url_rule('/reports/<group>/leaderboard/<int:months>/<person>/', 'report_leaderboard', report_leaderboard)
app.add_url_rule('/reports/<group>/leaderboard/<int:start_year>-<int:start_month>/<int:months>/<person>', 'report_leaderboard', report_leaderboard)
app.add_url_rule('/login/', 'login', login, methods=["GET", "POST"])
app.add_url_rule('/logout/', 'logout', logout)
app.add_url_rule('/person/<name>/', 'person', person)
app.add_url_rule('/quick/', 'quick', quick, methods=["GET"])
app.add_url_rule('/robots.txt', 'robots', robots,)
app.add_url_rule('/team/<team_slug>/', 'team', team)
app.add_url_rule('/team/<team_slug>/backlog/', 'team_backlog', team_backlog, methods=["GET", "POST"])
app.add_url_rule('/funnel/<state_slug>/', 'funnel', funnel, methods=["GET", "POST"])
app.add_url_rule('/favicon.ico', 'favicon', favicon)
