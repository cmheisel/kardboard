import sys

import logging
logging.basicConfig(level=logging.INFO)

from kardboard.models import Kard
from kardboard.tasks import update_ticket

key = sys.argv[1]

kard = Kard.objects.get(key=key)
update_ticket.apply((kard.id,))
