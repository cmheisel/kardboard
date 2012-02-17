import datetime

from dateutil import relativedelta

from kardboard.models import Kard, Person
from flask.ext.celery import Celery
from kardboard.app import app

celery = Celery(app)


@celery.task(name="tasks.force_update_ticket", ignore_result=True)
def force_update_ticket(card_id):
    logger = force_update_ticket.get_logger()
    k = Kard.objects.with_id(card_id)
    k.ticket_system.actually_update()
    logger.info("FORCED UPDATE on %s" % k.key)


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
        local_updated = k.ticket_system_data.get('updated', None)

        should_update = False
        if not local_updated:
            # We've never sync'd before, time to do it right now
            should_update = True
        elif origin_updated:
            if local_updated < origin_updated:
                logger.info(
                    "%s UPDATED on origin: Local: %s < Origin: %s" % (k.key, local_updated, origin_updated)
                )
                should_update = True
            else:
                k._ticket_system_updated_at = datetime.datetime.now()
                k.save()
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
                logger.info(
                    "%s FORCED UPDATE because no origin update date available")

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
    logger.info(
        "Looking for cards that haven't been updated since %s" % (old_time, )
    )

    old_cards = Kard.objects.filter(_ticket_system_updated_at__lte=old_time, done_date=None).order_by('_ticket_system_updated_at')
    old_done_cards = Kard.objects.done().filter(_ticket_system_updated_at__lte=old_time).order_by('_ticket_system_updated_at')

    [update_ticket.delay(k.id) for k in new_cards]
    [update_ticket.delay(k.id) for k in old_cards.limit(150)]
    [update_ticket.delay(k.id) for k in old_done_cards.limit(50)]

    logger.info(
        "Queued updates -- NEW: %s EXISTING: %s DONE: %s" % (
            len(new_cards), len(old_cards), len(old_done_cards)
        )
    )


@celery.task(name="tasks.update_daily_record", ignore_result=True)
def update_daily_record(target_date, group):
    from kardboard.models import DailyRecord

    logger = update_daily_record.get_logger()

    should_recalc = False

    # We need all this logic because this job can be pulled
    # by two workers in parallel leading to a race condition
    try:
        dr = DailyRecord.objects.get(date=target_date, group=group)
        one_minute_ago = datetime.datetime.now() - relativedelta.relativedelta(minutes=1)
        if dr.updated_at <= one_minute_ago:
            should_recalc = True
        else:
            logger.debug("DailyRecord: %s / %s was recalulcated in the last minute" % (target_date, group))
    except DailyRecord.DoesNotExist:
        should_recalc = True


    if should_recalc:
        try:
            DailyRecord.calculate(date=target_date, group=group)
            logger.info("Successfully calculated DailyRecord: Date: %s / Group: %s" % (target_date, group))
        except Exception:
            logger.warning("Tried to save duplicate record: Date: %s / Group: %s" % (target_date, group))
            raise



@celery.task(name="tasks.queue_daily_record_updates", ignore_result=True)
def queue_daily_record_updates(days=365):
    from kardboard.app import app
    from kardboard.util import make_end_date

    report_groups = app.config.get('REPORT_GROUPS', {})
    group_slugs = report_groups.keys()
    group_slugs.append('all')

    now = datetime.datetime.now()

    for i in xrange(0, days):
        target_date = now - relativedelta.relativedelta(days=i)
        target_date = make_end_date(date=target_date)
        for slug in group_slugs:
            update_daily_record.delay(target_date, slug)


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


@celery.task(name="tasks.jira_add_team_cards", ignore_result=True)
def jira_add_team_cards(team, filter_id):
    from kardboard.tickethelpers import JIRAHelper
    from kardboard.models import States

    logger = jira_add_team_cards.get_logger()
    logger.info("JIRA BACKLOG SYNC %s: %s" % (team, filter_id))
    states = States()
    helper = JIRAHelper(app.config, None)
    issues = helper.service.getIssuesFromFilter(helper.auth, filter_id)
    for issue in issues:
        if Kard.objects.filter(key=issue.key):
            # Card exists, pass
            pass
        else:
            logger.info("JIRA BACKLOGGING %s: %s" % (team, issue.key))
            defaults = {
                'key': issue.key,
                'title': issue.summary,
                'backlog_date': datetime.datetime.now(),
                'team': team,
                'state': states.backlog,
            }
            c = Kard(**defaults)
            c.ticket_system.actually_update(issue)
            c.save()


@celery.task(name="tasks.jira_queue_team_cards", ignore_result=True)
def jira_queue_team_cards():
    team_filters = app.config.get('JIRA_TEAM_FILTERS', ())
    for team, filter_id in team_filters:
        jira_add_team_cards.delay(team, filter_id)
