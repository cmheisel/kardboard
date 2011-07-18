from kardboard.models import Kard
from kardboard.tasks import update_ticket

for k in Kard.objects.all():
    update_ticket.apply_async((k.id,))
