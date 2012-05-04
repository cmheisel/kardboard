MONGODB_DB = 'kardboard'

MONGODB_PORT = 27017

SECRET_KEY = 'yougonnawannachangethis'

CACHE_TYPE = 'simple'
CACHE_DEFAULT_TIMEOUT = 3600


CARD_STATES = [
    'Todo',
    'Doing',
    'Done',
]

BACKLOG_STATE = 0
START_STATE = 1
DONE_STATE = -1

CARD_TEAMS = [
    'Team 1',
    'Team 2',
]

REPORT_GROUPS = {
    # key is slug
    # value is two item tuple, first item is tuple of team strings, second item is display name for report group
    'team-1': (('Team 1',), 'Team 1'),
    'team-2': (('Team 2',), 'Team 2'),
}

DEFAULT_CLASS = "Card"

BROKER_TRANSPORT = "redis"
BROKER_HOST = "localhost"  # Maps to redis host.
BROKER_PORT = 6379         # Maps to redis port.
BROKER_VHOST = "0"         # Maps to database number.

CELERYD_LOG_LEVEL = 'WARNING'
CELERYBEAT_LOG_LEVEL = CELERYD_LOG_LEVEL
CELERY_RESULT_BACKEND = "redis"
CELERY_REDIS_HOST = "localhost"
CELERY_REDIS_PORT = 6379
CELERY_REDIS_DB = 0
CELERY_IGNORE_RESULT = True
CELERY_IMPORTS = ('kardboard.tasks', )

TICKET_HELPER = 'kardboard.tickethelpers.NullHelper'
TICKET_AUTH = False

# How old can tickets get before we refresh
TICKET_UPDATE_THRESHOLD = 60 * 5

from celery.schedules import crontab
CELERYBEAT_SCHEDULE = {
    # How often should we look for old tickets and queue them for updates
    'load-update-queue': {
        'task': 'tasks.queue_updates',
        'schedule': crontab(minute="*/2"),
    },
    'jira_queue_team_cards': {
        'task': 'tasks.jira_queue_team_cards',
        'schedule': crontab(minute="*/3"),
    },
    # How often should we update all the Person
    # objects to make sure they reflect reality, due to deleted cards
    # or people being removed from a card
    'update_person': {
        'task': 'tasks.normalize_people',
        'schedule': crontab(minute="*/4"),
    },
    # How often (probably nighly) should we update daily records for the past
    # 365 days
    'calc-daily-records-year': {
        'task': 'tasks.queue_daily_record_updates',
        'schedule': crontab(minute=1, hour=0),
        'args': (365, ),
    },
    # How often should we update daily records for the past
    # 14 days
    'calc-daily-records-week': {
        'task': 'tasks.queue_daily_record_updates',
        'schedule': crontab(minute="*/5"),
        'args': (14, ),
    },
    # Capture/update the day's flow data
    'update_flow_reports': {
        'task': 'tasks.update_flow_reports',
        'schedule': crontab(minute="*/5"),
    }
}

