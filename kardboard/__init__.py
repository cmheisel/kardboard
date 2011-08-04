import os

from flask import Flask
from flaskext.cache import Cache
from flaskext.celery import Celery

from kardboard.util import PortAwareMongoEngine, slugify, timesince, configure_logging

__version__ = "1.3.4"

def get_app():
    app = Flask(__name__)
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
celery = Celery(app)


import kardboard.views
