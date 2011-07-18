from kardboard import celery
from kardboard.models import Kard


@celery.task()
def update_ticket(card_id):
    logger = update_ticket.get_logger()
    try:
        k = Kard.objects.with_id(card_id)
        logger.info("update_ticket running for %s" % (k.key, ))
        k.ticket_system.actually_update()
    except Kard.DoesNotExist:
        logger.error(
            "update_ticket: Kard with id %s does not exist" % (card_id, ))
