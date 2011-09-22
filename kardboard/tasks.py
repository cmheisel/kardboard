import datetime

from dateutil import relativedelta

from kardboard.models import Kard, Person
from flaskext.celery import Celery
from kardboard.app import app

celery = Celery(app)


@celery.task(name="tasks.update_ticket", ignore_result=True)
def update_ticket(card_id):
    from kardboard.app import app
    threshold = app.config.get('TICKET_UPDATE_THRESHOLD', 60 * 60)
    now = datetime.datetime.now()

    logger = update_ticket.get_logger()
    try:
        k = Kard.objects.with_id(card_id)
        diff = None
        if k._ticket_system_updated_at:
            diff = now - k._ticket_system_updated_at
        if not diff or diff and diff.seconds >= threshold:
            logger.info("update_ticket running for %s" % (k.key, ))
            try:
                k.ticket_system.actually_update()
            except AttributeError:
                logger.warn('Updating kard: %s and we got an AttributeError' % k.key)
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

    now = datetime.datetime.now()

    for i in xrange(0, days):
        target_date = now - relativedelta.relativedelta(days=i)
        DailyRecord.calculate(target_date)


@celery.task(name="tasks.normalize_people", ignore_result=True)
def normalize_people():
    """
    Data migration that sets up the initial set of Person
    objects. After this is run they'll be created
    and updated by the actually_update method of
    a card's ticket helper.
    """
    logger = normalize_people.get_logger()

    for k in Kard.objects.all():
        logger.debug("Condiering %s" % k.key)
        reporter = k.ticket_system_data.get('reporter', '')
        devs = k.ticket_system_data.get('developers', [])
        testers = k.ticket_system_data.get('qaers', [])

        logger.debug("Reporter: %s / Devs: %s / Testers: %s" % (reporter, devs, testers))

        if reporter:
            try:
                p = Person.objects.get(name=reporter)
            except Person.DoesNotExist:
                p = Person(name=reporter)

            p.report(k)
            p.save()

        for d in devs:
            try:
                p = Person.objects.get(name=d)
            except Person.DoesNotExist:
                p = Person(name=d)

            p.develop(k)
            p.save()

        for t in testers:
            try:
                p = Person.objects.get(name=t)
            except Person.DoesNotExist:
                p = Person(name=t)

            p.test(k)
            p.save()

