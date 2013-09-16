import sys
from kardboard.models.kard import Kard

key = sys.argv[1]

kard = Kard.objects.get(key=key.strip())

print kard.key
print kard.state
print kard.ticket_system_data['status']['name']
kard = kard.ticket_system.update_state(kard)
print kard.state
kard.save()