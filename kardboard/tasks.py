import datetime

from kardboard import celery
from kardboard.models import Kard


@celery.task(name="tasks.update_ticket", ignore_result=True)
def update_ticket(card_id):
    from kardboard import app
    threshold = app.config.get('TICKET_UPDATE_THRESHOLD', 60*60)
    now = datetime.datetime.now()

    logger = update_ticket.get_logger()
    try:
        k = Kard.objects.with_id(card_id)
        diff = None
        if k._ticket_system_updated_at:
            diff = now - k._ticket_system_updated_at
        if not diff or diff and diff.seconds >= threshold:
            logger.info("update_ticket running for %s" % (k.key, ))
            k.ticket_system.actually_update()
    except Kard.DoesNotExist:
        logger.error(
            "update_ticket: Kard with id %s does not exist" % (card_id, ))


@celery.task(name="tasks.queue_updates", ignore_result=True)
def queue_updates():
    from kardboard import app

    logger = queue_updates.get_logger()
    new_cards = Kard.objects.filter(_ticket_system_updated_at__not__exists=True)

    now = datetime.datetime.now()
    old_time = now - datetime.timedelta(seconds=app.config.get('TICKET_UPDATE_THRESHOLD', 60*60))

    old_cards = Kard.objects.filter(_ticket_system_updated_at__lte=old_time).order_by('_ticket_system_updated_at')

    [ update_ticket.delay(k.id) for k in new_cards ]
    [ update_ticket.delay(k.id) for k in old_cards.limit(50) ]

    logger.info("Queued updates for %s new and %s old tickets" %
        (new_cards.count(), old_cards.count()))
