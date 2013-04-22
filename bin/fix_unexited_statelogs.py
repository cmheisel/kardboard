from kardboard.models.kard import Kard
from kardboard.models.statelog import StateLog

unexited_logs = StateLog.objects.filter(exited__exists=False, state__nin=["Done", ])

fix_count = 0
for unexited_log in unexited_logs:
    try:
        k = Kard.objects.get(key=unexited_log.card.key)
    except AttributeError:
        print "MISSING CARD"
        pass
    logs = StateLog.objects.filter(card=k)
    for l in logs:
        if l.exited is None:
            for log in StateLog.objects.filter(card=k):
                if log.state == l.state and log.entered > l.entered:
                    #print "%s" % l.card.key
                    fix_count +=1
                    l.exited = log.entered
                    l.save()


print "Fixed: %s" % (fix_count)
