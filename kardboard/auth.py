import functools

from flask import (
    redirect,
    url_for,
    session,
)


def login_required(func):
    @functools.wraps(func)
    def login_checking_func(*args, **kwargs):
        from kardboard.app import app
        from flask import request

        authenticated = True
        if app.config.get('TICKET_AUTH', False):
            if 'username' in session:
                authenticated = True
            else:
                authenticated = False

        if authenticated:
            return func(*args, **kwargs)
        else:
            url = url_for('login', next=request.url)
            return redirect(url)
    return login_checking_func
