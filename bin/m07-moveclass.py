from kardboard.models import Kard

for k in Kard.objects.all().only('_type', '_service_class'):
    if k._type is None:
        if k._service_class is not None:
            k._type = k._service_class
            k._service_class = None
            k.update(set___type=k._type, set___service_class=k._service_class)
