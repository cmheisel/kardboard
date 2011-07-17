import os

from flask import Flask
from flaskext.mongoengine import MongoEngine
from flaskext.cache import Cache
import mongoengine

__version__ = "1.3.3"

app = Flask(__name__)


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
app.secret_key = app.config['SECRET_KEY']
app.db = PortAwareMongoEngine(app)

from kardboard.util import slugify
app.jinja_env.filters['slugify'] = slugify
cache = Cache(app)

import kardboard.views
