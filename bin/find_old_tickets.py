import logging

from kardboard.tasks import queue_updates

logging.basicConfig(level=logging.DEBUG)
queue_updates.apply()
