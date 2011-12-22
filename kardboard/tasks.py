import datetime

from dateutil import relativedelta

from kardboard.models import Kard, Person
from flask.ext.celery import Celery
from kardboard.app import app

celery = Celery(app)


@celery.task(name="tasks.update_ticket", ignore_result=True)
def update_ticket(card_id):
    from kardboard.app import app

    logger = update_ticket.get_logger()
    try:
        # We want to update cards if their local update time
        # is less than their origin update time
        k = Kard.objects.with_id(card_id)
        i = k.ticket_system.get_issue(k.key)
        origin_updated = getattr(i, 'updated')
        local_updated = k._ticket_system_updated_at

        should_update = False
        if not local_updated:
            # We've never sync'd before, time to do it right now
            should_update = True
        elif origin_updated:
            if local_updated < origin_updated:
                logger.info(
                    "%s UPDATED on origin: %s < %s" % (k.key, local_updated, origin_updated)
                )
                should_update = True
        else:
            # Ok well something changed with the ticket system
            # so we need fall back to the have we updated
            # from origin in THRESHOLD seconds, regardless
            # of how long ago the origin was updated
            # less efficient, but it guarantees updates
            threshold = app.config.get('TICKET_UPDATE_THRESHOLD', 60 * 60)
            now = datetime.datetime.now()
            diff = now - local_updated
            if diff.seconds >= threshold:
                should_update = True

        if should_update:
            logger.info("update_ticket running for %s" % (k.key, ))
            try:
                k.ticket_system.actually_update()
            except AttributeError:
                logger.warning('Updating kard: %s and we got an AttributeError' % k.key)
                raise

    except Kard.DoesNotExist:
        logger.error(
            "update_ticket: Kard with id %s does not exist" % (card_id, ))


@celery.task(name="tasks.queue_updates", ignore_result=True)
def queue_updates():
    from kardboard.app import app

    logger = queue_updates.get_logger()
    new_cards = Kard.objects.filter(_ticket_system_updated_at__not__exists=True)

    now = datetime.datetime.now()
    old_time = now - datetime.timedelta(seconds=app.config.get('TICKET_UPDATE_THRESHOLD', 60 * 60))

    old_cards = Kard.objects.filter(_ticket_system_updated_at__lte=old_time, done_date=None).order_by('_ticket_system_updated_at')
    old_done_cards = Kard.objects.done().filter(_ticket_system_updated_at__lte=old_time).order_by('_ticket_system_updated_at')

    [update_ticket.delay(k.id) for k in new_cards]
    [update_ticket.delay(k.id) for k in old_cards.limit(100)]
    [update_ticket.delay(k.id) for k in old_done_cards.limit(50)]

    logger.info("Queued updates -- NEW: %s EXISTING: %s DONE: %s" %
        (new_cards.count(), old_cards.count(), old_done_cards.count()))


@celery.task(name="tasks.update_daily_records", ignore_result=True)
def update_daily_records(days=365):
    from kardboard.models import DailyRecord
    from kardboard.app import app

    report_groups = app.config.get('REPORT_GROUPS', {})
    group_slugs = report_groups.keys()
    group_slugs.append('all')

    now = datetime.datetime.now()

    for i in xrange(0, days):
        target_date = now - relativedelta.relativedelta(days=i)
        for slug in group_slugs:
            DailyRecord.calculate(target_date, group=slug)


def _get_person(name, cache):
    p = cache.get(name, None)
    if not p:
        try:
            p = Person.objects.get(name=name)
        except Person.DoesNotExist:
            p = Person(name=name)
        cache[name] = p
    return p


@celery.task(name="tasks.normalize_people", ignore_result=True)
def normalize_people():
    """
    Data migration that sets up the initial set of Person
    objects. After this is run they'll be created
    and updated by the actually_update method of
    a card's ticket helper.
    """
    logger = normalize_people.get_logger()
    people_cache = {}

    for k in Kard.objects.all():
        logger.debug("Considering %s" % k.key)
        reporter = k.ticket_system_data.get('reporter', '')
        devs = k.ticket_system_data.get('developers', [])
        testers = k.ticket_system_data.get('qaers', [])

        logger.debug("Reporter: %s / Devs: %s / Testers: %s" % (reporter, devs, testers))

        if reporter:
            p = _get_person(reporter, people_cache)
            p.report(k)

        for d in devs:
            p = _get_person(d, people_cache)
            p.develop(k)

        for t in testers:
            p = _get_person(t, people_cache)
            p.test(k)

    for name, person in people_cache.items():
        person.save()
