import os

from flask import Flask
from flaskext.cache import Cache

from kardboard.util import (
    PortAwareMongoEngine,
    slugify,
    timesince,
    configure_logging,
    LazyView,
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

    configure_logging(app)

    try:
        from flaskext.exceptional import Exceptional
    except ImportError:
        pass
    exceptional_key = app.config.get('EXCEPTIONAL_API_KEY', '')
    if exceptional_key:
        exceptional = Exceptional(app)
        app._exceptional = exceptional

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
url('/card/<key>/block/', 'card_block', methods=["GET", "POST"])
url('/card/export/', 'card_export')
url('/reports/', 'reports_index')
url('/reports/<group>/throughput/', 'chart_throughput')
url('/reports/<group>/throughput/<int:months>/', 'chart_throughput')
url('/reports/<group>/cycle/', 'chart_cycle')
url('/reports/<group>/cycle/<int:months>/', 'chart_cycle')
url('/reports/<group>/cycle/distribution/', 'chart_cycle_distribution')
url('/reports/<group>/cycle/distribution/<int:months>/', 'chart_cycle_distribution')
url('/reports/<group>/cycle/from/<int:year>/<int:month>/<int:day>/', 'chart_cycle')
url('/reports/<group>/flow/', 'chart_flow')
url('/reports/<group>/flow/<int:months>/', 'chart_flow')
url('/reports/<group>/done/', 'done')
url('/login/', 'login', methods=["GET", "POST"])
url('/logout/', 'logout')
url('/overview/', 'dashboard')
url('/overview/<int:year>/<int:month>/', 'dashboard')
url('/overview/<int:year>/<int:month>/<int:day>/', 'dashboard')
url('/person/<name>/', 'person')
url('/quick/', 'quick', methods=["GET"])
url('/robots.txt', 'robots')
url('/team/<team_slug>/', 'team')
