import pprint
import sys

from kardboard.models import Kard

k = Kard.objects.get(key=sys.argv[1])
i = k.ticket_system.get_issue(key=k.key)

pprint.pprint(i)
