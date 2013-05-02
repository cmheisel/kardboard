import os
import socket

import path
import statsd

from flask import Flask
from flaskext.cache import Cache
from flask.ext.mongoengine import MongoEngine
from jinja2 import ModuleLoader
try:
    from flask_debugtoolbar import DebugToolbarExtension
    DEBUG_TOOLBAR = True
except ImportError:
    DEBUG_TOOLBAR = False

try:
    from raven.contrib.flask import Sentry
    SENTRY_SUPPORT = True
except ImportError:
    SENTRY_SUPPORT = False

from kardboard.util import (
    slugify,
    timesince,
    timeuntil,
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

    app.db = MongoEngine(app)

    app.jinja_env.add_extension('kardboard.util.Markdown2Extension')
    app.jinja_env.filters['slugify'] = slugify
    app.jinja_env.filters['timesince'] = timesince
    app.jinja_env.filters['timeuntil'] = timeuntil
    app.jinja_env.filters['jsonencode'] = jsonencode
    app.jinja_env.globals['newrelic_head'] = newrelic_head
    app.jinja_env.globals['newrelic_foot'] = newrelic_foot


    if app.config.get('COMPILE_TEMPLATES', False):
        compiled_templates = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'compiled_templates')
        compiled_files = path.path(compiled_templates).files()
        if len(compiled_files) <= 1:
            app.jinja_env.compile_templates(compiled_templates, zip=None, py_compile=True)
        app.jinja_env.loader = ModuleLoader(compiled_templates)

    configure_logging(app)

    app.wsgi_app = FixGunicorn(app.wsgi_app)

    statsd_conf = app.config.get('STATSD_CONF', {})

    statsd_connection = statsd.Connection(
        host=statsd_conf.get('host', '127.0.0.1'),
        port=statsd_conf.get('port', 8125),
        sample_rate=statsd_conf.get('sample_rate', 1),
    )

    machine_name = socket.getfqdn().split('.')[0]
    environment_name = app.config.get('ENV_MAPPING', {}).get(machine_name, 'default')
    prefix_name = '%s.%s.kardboard' % (environment_name, machine_name)
    app.statsd = statsd.Client(prefix_name, statsd_connection)

    if SENTRY_SUPPORT and 'SENTRY_DSN' in app.config.keys():
        sentry = Sentry(app)
        sentry

    return app

app = get_app()
cache = Cache(app)

if DEBUG_TOOLBAR and app.config.get('DEBUG_TOOLBAR', False):
    toolbar = DebugToolbarExtension(app)
