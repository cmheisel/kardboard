from kardboard.models import Kard, Q
from kardboard.app import app

# First pass
for k in Kard.objects.all():
    k.save()

query = Q(_service_class=None) | Q(_service_class=app.config['DEFAULT_CLASS'])

still_bad = []
bad_kards = Kard.objects.filter(query)
for k in bad_kards:
    k.ticket_system.update(sync=True)
    k.save()
    if k.service_class == app.config['DEFAULT_CLASS']:
        still_bad.append(k)

type_ids = {}
for k in still_bad:
    type_id, key = k.key, k.ticket_system.get_issue(k.key)['type']
    type_ids.get(type_id, []).append(key)

print type_ids
