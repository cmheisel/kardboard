from kardboard.models import FlowReport

for f in FlowReport.objects.all():
    for state in f.data:
        f.state_counts[state['name']] = state['count']
    del f.data
    f.save()
