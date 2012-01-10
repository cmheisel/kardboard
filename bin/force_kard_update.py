from kardboard.models import Kard
from kardboard.tasks import force_update_ticket

for k in Kard.in_progress():
    force_update_ticket.delay(k.id)
print "Queued updates for %s WIP cards" % (Kard.in_progress().count())

for k in Kard.backlogged():
    force_update_ticket.delay(k.id)
print "Queued updates for %s backlogged cards" % (Kard.backlogged().count())

for k in Kard.objects.done():
    force_update_ticket.delay(k.id)
print "Queued updates for %s done cards" % (Kard.objects.done().count())
