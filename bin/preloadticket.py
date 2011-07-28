from kardboard.models import Kard
from kardboard.tasks import update_ticket

for k in Kard.objects.all():
    if not k._ticket_system_data:
        print "Scheduling update for %s" % k.key
        update_ticket.apply_async((k.id,))
