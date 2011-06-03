import os

from flask import Flask
from flaskext.mongoengine import MongoEngine

__version__ = "0.1"

app = Flask(__name__)
app.config.from_object('kardboard.default_settings')
if os.getenv('KARDBOARD_SETTINGS', None):
    app.config.from_envvar('KARDBOARD_SETTINGS')
app.db = MongoEngine(app)

if __name__ == "__main__":
    app.run()
