from pyramid.config import Configurator

from kardboard.version import version


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    settings['version'] = version
    config = Configurator(settings=settings)

    from mongoengine import connect
    connect(settings['mongodb_name'])

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('card_detail', '/card/{key}/')
    config.scan()
    return config.make_wsgi_app()
