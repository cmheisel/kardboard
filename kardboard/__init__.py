import os

from flask import Flask
from flaskext.mongoengine import MongoEngine
from flaskext.cache import Cache
from flaskext.celery import Celery
import mongoengine
import logging

__version__ = "1.3.3"

app = Flask(__name__)

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

class PortAwareMongoEngine(MongoEngine):
    def init_app(self, app):
        db = app.config['MONGODB_DB']
        username = app.config.get('MONGODB_USERNAME', None)
        password = app.config.get('MONGODB_PASSWORD', None)
        port = app.config.get('MONGODB_PORT', 27017)

        # more settings e.g. port etc needed

        self.connection = mongoengine.connect(
            db=db, username=username, password=password, port=port)

app.config.from_object('kardboard.default_settings')
if os.getenv('KARDBOARD_SETTINGS', None):
    app.config.from_envvar('KARDBOARD_SETTINGS')

if app.config.get('LOG_FILE'):
    log_file = app.config['LOG_FILE']
    log_file = os.path.abspath(os.path.expanduser(log_file))
    new_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=100000, backupCount=3)
    if app.config.get('LOG_LEVEL'):
        new_level = app.config['LOG_LEVEL']
        new_level = LEVELS.get(new_level, logging.error)
        new_handler.setLevel(new_level)

    log_format = (
        '-' * 80 + '\n' +
        '%(asctime)-15s\n%(levelname)s in %(module)s [%(pathname)s:%(lineno)d]:\n' +
        '%(message)s\n' +
        '-' * 80
    )
    new_handler.setFormatter(logging.Formatter(log_format))

    app.logger.addHandler(new_handler)


app.secret_key = app.config['SECRET_KEY']
app.db = PortAwareMongoEngine(app)

from kardboard.util import slugify
app.jinja_env.filters['slugify'] = slugify
cache = Cache(app)
celery = Celery(app)

import kardboard.views
