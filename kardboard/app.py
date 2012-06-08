import os

from flask import Flask
from flaskext.cache import Cache

from kardboard.util import (
    PortAwareMongoEngine,
    slugify,
    timesince,
    jsonencode,
    configure_logging,
    newrelic_head,
    newrelic_foot,
    FixGunicorn
)


def get_app():
    app = Flask('kardboard')
    app.config.from_object('kardboard.default_settings')
    if os.getenv('KARDBOARD_SETTINGS', None):
        app.config.from_envvar('KARDBOARD_SETTINGS')

    app.secret_key = app.config['SECRET_KEY']

    app.db = PortAwareMongoEngine(app)

    app.jinja_env.add_extension('kardboard.util.Markdown2Extension')
    app.jinja_env.filters['slugify'] = slugify
    app.jinja_env.filters['timesince'] = timesince
    app.jinja_env.filters['jsonencode'] = jsonencode
    app.jinja_env.globals['newrelic_head'] = newrelic_head
    app.jinja_env.globals['newrelic_foot'] = newrelic_foot

    configure_logging(app)

    try:
        from flaskext.exceptional import Exceptional
    except ImportError:
        pass
    exceptional_key = app.config.get('EXCEPTIONAL_API_KEY', '')
    if exceptional_key:
        exceptional = Exceptional(app)
        app._exceptional = exceptional

    app.wsgi_app = FixGunicorn(app.wsgi_app)

    return app

app = get_app()
cache = Cache(app)


from kardboard.views import (
    card,
    card_add,
    card_edit,
    card_delete,
    card_block,
    card_export,
    reports_index,
    report_throughput,
    report_cycle,
    report_cycle_distribution,
    report_flow,
    report_detailed_flow,
    done,
    report_service_class,
    report_leaderboard,
    login,
    logout,
    dashboard,
    person,
    quick,
    robots,
    favicon,
    state,
    team,
)

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
app.add_url_rule('/reports/<group>/cycle/distribution/', 'report_cycle_distribution', report_cycle_distribution)
app.add_url_rule('/reports/<group>/cycle/distribution/<int:months>/', 'report_cycle_distribution', report_cycle_distribution)
app.add_url_rule('/reports/<group>/flow/', 'report_flow', report_flow)
app.add_url_rule('/reports/<group>/flow/<int:months>/', 'report_flow', report_flow)
app.add_url_rule('/reports/<group>/flow/detail/', 'report_detailed_flow', report_detailed_flow)
app.add_url_rule('/reports/<group>/flow/detail/<int:months>/', 'report_detailed_flow', report_detailed_flow)
app.add_url_rule('/reports/<group>/done/', 'done', done)
app.add_url_rule('/reports/<group>/done/<int:months>/', 'done', done)
app.add_url_rule('/reports/<group>/classes/', 'report_service_class', report_service_class)
app.add_url_rule('/reports/<group>/classes/<int:months>/', 'report_service_class', report_service_class)
app.add_url_rule('/reports/<group>/leaderboard/', 'report_leaderboard', report_leaderboard)
app.add_url_rule('/reports/<group>/leaderboard/<int:months>/', 'report_leaderboard', report_leaderboard)
app.add_url_rule('/reports/<group>/leaderboard/<int:start_year>-<int:start_month>/<int:months>/', 'report_leaderboard', report_leaderboard)
app.add_url_rule('/reports/<group>/leaderboard/<int:months>/<person>/', 'report_leaderboard', report_leaderboard)
app.add_url_rule('/reports/<group>/leaderboard/<int:start_year>-<int:start_month>/<int:months>/<person>', 'report_leaderboard', report_leaderboard)
app.add_url_rule('/login/', 'login', login, methods=["GET", "POST"])
app.add_url_rule('/logout/', 'logout', logout)
app.add_url_rule('/overview/', 'dashboard', dashboard)
app.add_url_rule('/overview/<int:year>/<int:month>/', 'dashboard', dashboard)
app.add_url_rule('/overview/<int:year>/<int:month>/<int:day>/', 'dashboard', dashboard)
app.add_url_rule('/person/<name>/', 'person', person)
app.add_url_rule('/quick/', 'quick', quick, methods=["GET"])
app.add_url_rule('/robots.txt', 'robots', robots,)
app.add_url_rule('/team/<team_slug>/', 'team', team)
app.add_url_rule('/favicon.ico', 'favicon', favicon)
