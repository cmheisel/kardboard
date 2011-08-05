from datetime import timedelta


MONGODB_DB = "kardboard"

MONGODB_PORT = 27017

SECRET_KEY = "yougonnawannachangethis"

CACHE_TYPE = 'simple'

CARD_CATEGORIES = [
    "Bug",
    "Feature",
    "Improvement",
]

STATES = [
    'Todo',
    'Doing',
    'Done',
]

BROKER_TRANSPORT = "mongodb"
CELERY_RESULT_BACKEND = "mongodb"
CELERY_MONGODB_BACKEND_SETTINGS = {
    "database": MONGODB_DB,
    "taskmeta_collection": "kardboard_taskmeta",
}
CELERY_IMPORTS = ("kardboard.tasks", )



CELERYD_LOG_LEVEL = "INFO"
BROKER_TRANSPORT = "mongodb"
CELERY_RESULT_BACKEND = "mongodb"
CELERY_MONGODB_BACKEND_SETTINGS = {
    "database": MONGODB_DB,
    "taskmeta_collection": "kardboard_taskmeta",
}
CELERY_IMPORTS = ("kardboard.tasks", )



TICKET_HELPER = "kardboard.tickethelpers.NullHelper"

# How old can tickets get before we refresh
TICKET_UPDATE_THRESHOLD = 60*5

# How often should we look for old tickets and queue them for updates
CELERYBEAT_SCHEDULE = {
    "load-update-queue": {
        "task": "tasks.queue_updates",
        "schedule": timedelta(seconds=90),
    },
}
