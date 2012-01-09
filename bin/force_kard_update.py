from kardboard.models import Kard
from kardboard.tasks import force_update_ticket

for k in Kard.objects.all():
    force_update_ticket.delay(k.id)

print "Queued updates for %s cards" % (Kard.objects.count())