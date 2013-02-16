from kardboard.models.kard import Kard
from kardboard.models.statelog import StateLog

bad_logs = StateLog.objects.filter(exited__exists=False, state__nin=["Done", ])
for bad_log in bad_logs:
    k = Kard.objects.get(key=bad_log.card.key)
    logs = StateLog.objects.filter(card=k)
    for l in logs:
        if l.exited is None:
            for log in StateLog.objects.filter(card=k):
                #print "%s %s %s %s" % (log.card.key, log.state, log.entered, log.exited)
                if log.state == l.state and log.entered > l.entered:
                    l.exited = log.entered
                    l.save()
