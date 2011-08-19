from datetime import timedelta

MONGODB_DB = 'kardboard'

MONGODB_PORT = 27017

SECRET_KEY = 'yougonnawannachangethis'

CACHE_TYPE = 'simple'
CACHE_DEFAULT_TIMEOUT = 3600


CARD_CATEGORIES = [
    'Bug',
    'Feature',
    'Improvement',
]

CARD_STATES = [
    'Todo',
    'Doing',
    'Done',
]

CARD_TEAMS = [
    'Team 1',
    'Team 2',
]


CELERYD_LOG_LEVEL = 'INFO'
BROKER_TRANSPORT = 'mongodb'
CELERY_RESULT_BACKEND = 'mongodb'
CELERY_MONGODB_BACKEND_SETTINGS = {
    'database': MONGODB_DB,
    'taskmeta_collection': 'kardboard_taskmeta',
}
CELERY_IMPORTS = ('kardboard.tasks', )

TICKET_HELPER = 'kardboard.tickethelpers.NullHelper'

# How old can tickets get before we refresh
TICKET_UPDATE_THRESHOLD = 60 * 10

CELERYBEAT_SCHEDULE = {
    # How often should we look for old tickets and queue them for updates
    'load-update-queue': {
        'task': 'tasks.queue_updates',
        'schedule': timedelta(seconds=90),
    },
    # How often (probably nighly) should we update daily records for the past
    # 365 days
    'calc-daily-records-year': {
        'task': 'tasks.update_daily_records',
        'schedule': timedelta(seconds=86400),
        'args': (365, ),
    },
    # How often should we update daily records for the past
    # 7 days
    'calc-daily-records-week': {
        'task': 'tasks.update_daily_records',
        'schedule': timedelta(seconds=90),
        'args': (7, ),
    }
}
