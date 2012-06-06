import os

hostname = os.uname()[1]

app_environment = 'production'
nr_ini = "/home/kardboard/kardboardve/etc/newrelic.ini"

import newrelic.agent
newrelic.agent.initialize(nr_ini, app_environment)

from kardboard.app import app