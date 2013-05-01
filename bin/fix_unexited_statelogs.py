from kardboard.models.kard import Kard
from kardboard.models.statelog import StateLog

unexited_logs = StateLog.objects.filter(exited__exists=False, state__nin=["Done", "Backlog", ])

fix_count = 0
for unexited_log in unexited_logs:
    try:
        k = Kard.objects.get(key=unexited_log.card.key)
    except AttributeError:
        print "MISSING CARD"
        pass
    for log in StateLog.objects.filter(card=k, entered__gt=unexited_log.entered).order_by('entered').limit(1):
            print "APPLYING %s - %s - %s" % (log.card.key, log.state, log.entered)
            print "\t %s - %s - %s - %s" % (unexited_log.card.key, unexited_log.state, unexited_log.entered, log.exited)
            fix_count +=1
            unexited_log.exited = log.entered
            unexited_log.save()


print "Fixed: %s" % (fix_count)
