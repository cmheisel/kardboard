=====================
Installing Kardboard
=====================

.. todo::

    Document Nginx, Gunicorn, Celery configuration for a deployment.

Settings & Configuration
==========================
Much of kardboard can be controlled via settings. The easiest way control these is add an environment variable, **KARDBOARD_SETTINGS**, that is a path to a .cfg file containing these settings. ::

    export KARDBOARD_SETTINGS=/opt/www/kardboardve/etc/kardboard-prod.conf

The config file should be in a format compatible with `Flask's file-based configuration standard <http://flask.pocoo.org/docs/config/#configuring-from-files>`_.


Flask settings
---------------

Kardboard is built atop `Flask <http://flask.pocoo.org>`_ and as such all of its `built in options <http://flask.pocoo.org/docs/config/#builtin-configuration-values>`_ can be adjusted in your configuration file.

Kardboard settings
-------------------

All the necessary settings to get a basic kardboard instance up and running are contained in kardboard/default_settings.py

CACHE_TYPE
^^^^^^^^^^^
Default: ``'simple'``
Specifies which type of caching object to use. This is an import string that will be imported and instantiated. It is assumed that the import object is a function that will return a cache object that adheres to the werkzeug cache API.

For werkzeug.contrib.cache objects, you do not need to specify the entire import string, just one of the following names.

Built-in cache types:

* **null**: NullCache
* **simple**: SimpleCache
* **memcached**: MemcachedCache
* **gaememcached**: GAEMemcachedCache
* **filesystem**: FileSystemCache

CACHE_ARGS
^^^^^^^^^^^
Default: ``[]`` (Empty list)

Optional list to unpack and pass during the cache class instantiation.

CACHE_OPTIONS
^^^^^^^^^^^^^^^
Default: ``{}`` (Empty dictionary)

Optional dictionary to pass during the cache class instantiation.

CACHE_DEFAULT_TIMEOUT
^^^^^^^^^^^^^^^^^^^^^^^
Default: ``3600``

The default timeout that is used if no timeout is specified. Unit of time is seconds.

CACHE_THRESHOLD
^^^^^^^^^^^^^^^^
Default: (No default)

The maximum number of items the cache will store before it starts deleting some. Used only for SimpleCache and FileSystemCache

CACHE_KEY_PREFIX
^^^^^^^^^^^^^^^^^^
Default: (No default)

A prefix that is added before all keys. This makes it possible to use the same memcached server for different apps. Used only for MemcachedCache and GAEMemcachedCache.

CACHE_MEMCACHED_SERVERS
^^^^^^^^^^^^^^^^^^^^^^^^^
Default: (No default)

A list or a tuple of server addresses. Used only for MemcachedCache

CACHE_DIR
^^^^^^^^^^
Default: (No default)

Directory to store cache. Used only for FileSystemCache.

.. _CARD_CATEGORIES:

CARD_CATEGORIES
^^^^^^^^^^^^^^^^^
Default: ``[ 'Bug', 'Feature', 'Improvement',]``

The list of categories users should be able to assign cards to. Example::

    CARD_CATEGORIES = [ 'CMS', 'iPhone', 'Android', ]
    CARD_CATEGORIES = [ 'Project X', 'Project Y', 'Project Z']

CARD_STATES
^^^^^^^^^^^^^
Default: ``[ 'Todo', 'Doing', 'Done', ]``

The list of states, or columns, that a card could be in. **The last state should represent whatever Done means to your team.**

.. TIP::
    When a user sets a Done date for a card, it's automatically set to the last state in your CARD_STATES setting.

CELERYD_LOG_LEVEL
^^^^^^^^^^^^^^^^^^
Default: ``'INFO'``

See `Celery configuration documentation`_ for details

BROKER_TRANSPORT
^^^^^^^^^^^^^^^^
Default: ``'mongodb'``

See `Celery configuration documentation`_ for details

CELERY_RESULT_BACKEND
^^^^^^^^^^^^^^^^^^^^^^
Default: ``'mongodb'``

See `Celery configuration documentation`_ for details

CELERY_MONGODB_BACKEND_SETTINGS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Default::

    {
        'database': MONGODB_DB,
        'taskmeta_collection': 'kardboard_taskmeta',
    }

See `Celery configuration documentation`_ for details

CELERY_IMPORTS
^^^^^^^^^^^^^^^^
Default: ``('kardboard.tasks', )``

See `Celery configuration documentation`_ for details


.. _CELERYBEAT_SCHEDULE:

CELERYBEAT_SCHEDULE
^^^^^^^^^^^^^^^^^^^^^
Default::

    {
        'load-update-queue': {
            'task': 'tasks.queue_updates',
            'schedule': timedelta(seconds=90),
        },
    }

If you're using a :ref:`TICKET_HELPER` then you probably don't want to adjust this setting. The `timedelta(seconds=90)` determines how often kardboard should check for out of date cards. See  :ref:`TICKET_UPDATE_THRESHOLD` for more.

See `Celery configuration documentation`_ for details

GOOGLE_SITE_VERIFICATION
^^^^^^^^^^^^^^^^^^^^^^^^^^
Default: (No default)

If set, it will output an appropriate <meta> tag so you may claim your site on Google Webmaster Tools. ::

    GOOGLE_SITE_VERIFICATION = 'someverylongstringgoeshere'

GOOGLE_ANALYTICS
^^^^^^^^^^^^^^^^^
Default: (No default)

If set, it will output an appropriate <script> tag for Google Analytics. ::

    GOOGLE_ANALYTICS = 'UA-11111111-2'

JIRA_CREDENTIALS
^^^^^^^^^^^^^^^^^^
Default: (No default)

A two item tuple consisting of a username and password that has at least read-only access to any projects and tickets you'll be enterting into kardboard. ::

    JIRA_CREDENTIALS = ('jbluth', 'theresalwaysmoneyinthebananastand')


JIRA_WSDL
^^^^^^^^^^^
Default: (No default)

If you set :ref:`TICKET_HELPER` to use the built-in JIRAHelper then you'll want to set this to your JIRA installation's SOAP end point. ::

    JIRA_WSDL = 'https://jira.yourdomain.com/rpc/soap/jirasoapservice-v2?wsdl'

LOG_LEVEL
^^^^^^^^^^
Default: (No default)

The level of log events that should be output to :ref:`LOG_FILE`.

Possible settings are:

* ``'debug'``
* ``'info'``
* ``'warning'``
* ``'critical'``
* ``'error'``

.. _LOG_FILE:

LOG_FILE
^^^^^^^^^^
Default: (No default)

The file that log events should be written too. ::

    LOG_FILE = '/var/logs/kardboard-app.log'

.. NOTE::
    The LOG_FILE file will be automatically rotated every ~100k and up to 3 previous ~100k chunks will be kept.

MONGODB_DB
^^^^^^^^^^^^
Default: ``'kardboard'``

The name of the database you want to store your data in.

MONGODB_PORT
^^^^^^^^^^^^^^
Default: ``27017``

The port MongoDB is running on.

SECRET_KEY
^^^^^^^^^^^^
Default: ``'yougonnawannachangethis'``

A secret key for this particular kardboard instance. Used to provide a seed in secret-key hashing algorithms. Set this to a random string -- the longer, the better.

As the default implies, you're going to want to change this.


.. _TICKET_HELPER:

TICKET_HELPER
^^^^^^^^^^^^^^^
Default: ``'kardboard.tickethelpers.NullHelper'``

A Python class that will fetch additional information from a ticketing system (JIRA, Redmine, Pivotal Tracker, e.g.) about a card.

The only provider shipped with kardboard is ``'kardboard.tickethelpers.JIRAHelper'``.

.. _TICKET_UPDATE_THRESHOLD:

TICKET_UPDATE_THRESHOLD
^^^^^^^^^^^^^^^^^^^^^^^
Default: ``60*5`` (seconds)

The minimum length of time **in seconds** before a individual card has its data updated from its ticketing system of record.

Every 90 seconds (unless changed in :ref:`CELERYBEAT_SCHEDULE`), kardboard will scan for cards older than `TICKET_UPDATE_THRESHOLD` and fetch data on them.





.. _Celery configuration documentation: http://ask.github.com/celery/configuration.html