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
