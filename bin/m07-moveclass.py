from kardboard.models import Kard

for k in Kard.objects.all().only('_type', '_service_class'):
    if k._type is None:
        k._type = k._service_class
        k._service_class = None
        k.save()
