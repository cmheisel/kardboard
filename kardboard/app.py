import os

from flask import Flask
from flaskext.cache import Cache

from kardboard.util import (
    PortAwareMongoEngine,
    slugify,
    timesince,
    configure_logging,
    LazyView
)

from kardboard.version import __version__, VERSION


def get_app():
    app = Flask('kardboard')
    app.config.from_object('kardboard.default_settings')
    if os.getenv('KARDBOARD_SETTINGS', None):
        app.config.from_envvar('KARDBOARD_SETTINGS')

    app.secret_key = app.config['SECRET_KEY']

    app.db = PortAwareMongoEngine(app)

    app.jinja_env.filters['slugify'] = slugify
    app.jinja_env.filters['timesince'] = timesince

    configure_logging(app)

    return app

app = get_app()
cache = Cache(app)

def url(url_rule, import_name, **options):
    view = LazyView('kardboard.views.' + import_name)
    app.add_url_rule(url_rule, view_func=view, **options)


url('/', 'state')
url('/card/<key>/', 'card', methods=["GET", "POST"])
url('/card/add/', 'card_add', methods=["GET", "POST"])
url('/card/<key>/edit/', 'card_edit', methods=["GET", "POST"])
url('/card/<key>/delete/', 'card_delete', methods=["GET", "POST"])
url('/card/export/', 'card_export')
url('/chart/', 'chart_index')
url('/chart/throughput/', 'chart_throughput')
url('/chart/throughput/<int:months>/', 'chart_throughput')
url('/chart/cycle/', 'chart_cycle')
url('/chart/cycle/<int:months>/', 'chart_cycle')
url('/chart/cycle/from/<int:year>/<int:month>/<int:day>/', 'chart_cycle')
url('/chart/flow/', 'chart_flow')
url('/chart/flow/<int:months>/', 'chart_flow')
url('/done/', 'done')
url('/done/report/<int:year_number>/<int:month_number>/', 'done_report')
url('/overview/', 'dashboard')
url('/overview/<int:year>/<int:month>/', 'dashboard')
url('/overview/<int:year>/<int:month>/<int:day>/', 'dashboard')
url('/quick/', 'quick', methods=["GET"])
url('/robots.txt', 'robots')
url('/team/<team_slug>/', 'team')