from pyramid.httpexceptions import exception_response
from pyramid.view import view_config

@view_config(route_name='home', renderer='templates/home.pt')
def home(request):
    return {'project': 'kardboard'}

@view_config(route_name='card_detail', renderer='templates/card_detail.pt')
def card_detail(request, key=None):
    from kardboard.models.card import Card

    key = key or request.matchdict.get('key')
    try:
        card = Card.objects.get(key=key)
    except Card.DoesNotExist:
        return exception_response(404)
    return {'card': card}
