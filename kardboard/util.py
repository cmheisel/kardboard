import datetime
import re
import traceback
import logging
import os
import functools
import math

from logging.handlers import RotatingFileHandler

import jinja2.ext
import markdown2

from werkzeug.contrib.cache import RedisCache

import translitcodec
assert translitcodec
from dateutil.relativedelta import relativedelta


def average(values):
    """Computes the arithmetic mean of a list of numbers.

    >>> print average([20, 30, 70])
    40.0
    """
    if len(values) == 0:
        return float('nan')
    return sum(values, 0.0) / len(values)


def standard_deviation(values):
    avg = average(values)
    variance = map(lambda x: (x - avg)**2, values)
    standard_deviation = math.sqrt(average(variance))
    return standard_deviation


def delta_in_hours(delta):
    try:
        seconds = delta.total_seconds()
    except AttributeError:
        # We're in pythont 2.6
        seconds = delta.seconds
        days = delta.days
        seconds = seconds + (days * 24 * 60 * 60)

    hours = (seconds / 60.0) / 60.0
    hours = round(hours)
    return hours

class ImproperlyConfigured(Exception):
    pass


def redirect_to_next_url(fn):
    """
    Views wrapped in this decorator will
    look for a 'next_url' in the session or
    as a query string in the URL. If the view
    returns True (not a value that equates to True)
    then the user is redirected to next_url.
    """
    @functools.wraps(fn)
    def _wrapped_view_fn(*args, **kwargs):
        # Call the decorated function
        retval = fn(*args, **kwargs)

        if retval is True:
            from flask import redirect, request
            referrer = request.referrer if request.referrer and request.referrer.startswith(request.host_url) else None

            next_url = request.args.get('next', None) or referrer or "/"
            logging.debug("%s called with %s as NEXT" % (fn.__name__, next_url))
            return redirect(next_url)
        else:
            # Must not need the redirect, return the original return value
            return retval

    return _wrapped_view_fn


def redis_cache(app, args, kwargs):
    timeout = app.config.get('CACHE_DEFAULT_TIMEOUT', 300)
    return RedisCache(default_timeout=timeout)


def now():
    return datetime.datetime.now()


def get_current_app():
    from kardboard.app import app
    return app


def log_exception(exc, msg=""):
    tb = traceback.format_exc()
    log_msg = [msg, str(exc), tb]
    log_msg = '\n'.join(log_msg)
    app = get_current_app()
    app.logger.critical(log_msg)


def business_days_between(date1, date2):
    if date1 < date2:
        oldest_date, youngest_date = date1, date2
    else:
        oldest_date, youngest_date = date2, date1

    business_days = 0
    date = oldest_date
    while date < youngest_date:
        if date.weekday() != 5 and date.weekday() != 6:
            business_days += 1
        date = date + datetime.timedelta(days=1)
    return business_days


def month_ranges(date, num_months):
    if num_months == 1:
        return [month_range(date), ]
    end_start, end_end = month_range(date)
    months_ago = end_start - relativedelta(months=num_months - 1)

    start_start, start_end = month_range(months_ago)

    month_ranges = [(start_start, start_end), ]

    for i in xrange(0, num_months - 2):
        next_month = month_ranges[-1][0] + relativedelta(months=1)
        start, end = month_range(date=next_month)
        month_ranges.append((start, end))
    month_ranges.append((end_start, end_end))

    return month_ranges


def month_range(date):
    start = date.replace(day=1)
    end = start + relativedelta(months=+1) + relativedelta(days=-1)

    start, end = make_start_date(date=start), make_end_date(date=end)
    return start, end


def week_range(date):
    day_type = date.isoweekday()  # 1-7
    if day_type == 7:
        start_date = date
    else:
        start_date = date - relativedelta(days=day_type)
    end_date = start_date + relativedelta(days=6)

    start_date = make_start_date(date=start_date)
    end_date = make_end_date(date=end_date)

    return start_date, end_date


def make_start_date(year=None, month=None, day=None, date=None):
    start_date = munge_date(year, month, day, date)
    start_date = start_date.replace(hour=23, minute=59, second=59)
    start_date = start_date.replace(hour=0, minute=0, second=0)
    return start_date


def make_end_date(year=None, month=None, day=None, date=None):
    end_date = munge_date(year, month, day, date)
    end_date = end_date.replace(hour=23, minute=59, second=59)
    return end_date


def munge_date(year=None, month=None, day=None, date=None):
    """
    Takes a given datetime, or now(), and sets its
    year, month and day to any of those values passed in
    optionally.
    """
    if not date:
        date = datetime.datetime.now()

    year = year or date.year
    month = month or date.month
    day = day or date.day

    date = date.replace(year=year, month=month, day=day, microsecond=0)
    return date

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def slugify(text, delim=u'-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = word.encode('translit/long')
        if word:
            result.append(word)
    return unicode(delim.join(result))


def timesince(dt, default="just now"):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    """

    now = datetime.datetime.now()
    diff = now - dt

    periods = (
        (diff.days / 365, "year", "years"),
        (diff.days / 30, "month", "months"),
        (diff.days / 7, "week", "weeks"),
        (diff.days, "day", "days"),
        (diff.seconds / 3600, "hour", "hours"),
        (diff.seconds / 60, "minute", "minutes"),
        (diff.seconds, "second", "seconds"),
    )

    for period, singular, plural in periods:

        if period:
            return "%d %s ago" % (period, singular if period == 1 else plural)

    return default


def timeuntil(dt):
    """
    Returns string representing "time util" e.g.
    3 days, 5 hours, etc.
    """
    tardis = 'future'
    now = datetime.datetime.now()
    if dt < now:
        tardis = 'past'

    if tardis == 'future':
        diff = relativedelta(dt, now)
    elif tardis == 'past':
        diff = relativedelta(now, dt)

    msg = []
    if diff.months > 0:
        msg.append("%s months" % diff.months)
    if diff.days > 0:
        msg.append("%s days" % diff.days)
    if diff.hours > 0 and diff.days <= 0:
        msg.append("%s hours" % diff.hours)
    if diff.minutes > 0 and diff.hours <= 0:
        msg.append("%s minutes" % diff.minutes)

    if len(msg) > 1:
        msg = ', '.join(msg)
    elif len(msg) == 1:
        msg = ''.join(msg)

    if tardis == 'future':
        msg = "In %s" % msg
    elif tardis == 'past':
        msg = "%s ago" % msg

    if msg:
        return msg

    return dt.strftime("%m/%d/%Y")


def jsonencode(data):
    import json
    return json.dumps(data)


def get_newrelic():
    try:
        import newrelic
        return newrelic
    except ImportError:
        return None


def get_newrelic_agent():
    try:
        import newrelic.agent
        return newrelic.agent
    except ImportError:
        return None


def newrelic_head():
    agent = get_newrelic_agent()
    if agent:
        content = [
            '<!-- New Relic tracking -->'
        ]
        header = agent.get_browser_timing_header()
        content.append(header)
        return '\n'.join(content)
    return ''


def newrelic_foot():
    agent = get_newrelic_agent()
    if agent:
        content = [
            '<!-- New Relic tracking -->'
        ]
        footer = agent.get_browser_timing_footer()
        content.append(footer)
        return '\n'.join(content)
    return ''


def configure_logging(app):
    LEVELS = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}

    if app.config.get('LOG_FILE'):
        log_file = app.config['LOG_FILE']
        log_file = os.path.abspath(os.path.expanduser(log_file))
        new_handler = RotatingFileHandler(
            log_file, maxBytes=100000, backupCount=3)
        if app.config.get('LOG_LEVEL'):
            new_level = app.config['LOG_LEVEL']
            new_level = LEVELS.get(new_level, logging.error)
            new_handler.setLevel(new_level)

        log_format = (
            '-' * 80 + '\n' +
            '%(asctime)-15s\n%(levelname)s in %(module)s [%(pathname)s:%(lineno)d]:\n' +
            '%(message)s\n' +
            '-' * 80
        )
        new_handler.setFormatter(logging.Formatter(log_format))

        app.logger.addHandler(new_handler)


class Markdown2Extension(jinja2.ext.Extension):
    tags = set(['markdown2'])

    def __init__(self, environment):
        super(Markdown2Extension, self).__init__(environment)
        environment.extend(
            markdowner=markdown2.Markdown()
        )

    def parse(self, parser):
        lineno = parser.stream.next().lineno
        body = parser.parse_statements(
            ['name:endmarkdown2'],
            drop_needle=True
        )
        return jinja2.nodes.CallBlock(
            self.call_method('_markdown_support'),
            [],
            [],
            body
        ).set_lineno(lineno)

    def _markdown_support(self, caller):
        return self.environment.markdowner.convert(caller()).strip()


class FixGunicorn(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        environ['SERVER_PORT'] = str(environ['SERVER_PORT'])
        return self.app(environ, start_response)
