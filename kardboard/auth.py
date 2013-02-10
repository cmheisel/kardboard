import functools

from flask import (
    redirect,
    url_for,
    session,
)


def login_required(func):
    @functools.wraps(func)
    def login_checking_func(*args, **kwargs):
        from flask import request

        authenticated = is_authenticated()

        if authenticated:
            return func(*args, **kwargs)
        else:
            url = url_for('login', next=request.url)
            return redirect(url)
    return login_checking_func

def is_authenticated():
    from kardboard.app import app

    authenticated = True
    if app.config.get('TICKET_AUTH', False):
        if 'username' in session:
            authenticated = True
        else:
            authenticated = False

    return authenticated
