#!/usr/bin/env python

from __future__ import absolute_import
from flask.ext.script import Manager
from flask.ext.celery import Celery
from flask.ext.celery import install_commands as install_celery_commands

from kardboard.app import app

celery = Celery(app)
manager = Manager(app)
install_celery_commands(manager)

if __name__ == "__main__":
    manager.run()
