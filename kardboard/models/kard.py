import importlib
import datetime
import math

from dateutil.relativedelta import relativedelta

from kardboard.app import app

from mongoengine.queryset import Q
from flask.ext.mongoengine import QuerySet

from kardboard.models.blocker import BlockerRecord
from kardboard.models.states import States
from kardboard.services import ticketdatasync
from kardboard.util import (
    now,
    days_between,
    make_end_date,
    make_start_date,
    munge_date,
    month_range,
    week_range,
    average,
)

class KardQuerySet(QuerySet):
    def done_in_week(self, year=None, month=None, day=None, date=None):
        """
        Kards that were completed in the week of the specified day.
        """
        if not date:
            date = munge_date(year, month, day)
            date = make_end_date(date=date)
        start_date, end_date = week_range(date)

        results = self.done().filter(
            done_date__lte=date,
            done_date__gte=start_date
        )
        return results

    def average(self, field_str):
        values = [getattr(k, field_str) for k in self.filter().only(field_str)]
        return average(values)

    def distinct(self, field_str):
        return super(KardQuerySet, self).distinct(field_str)

    def moving_cycle_time(self, year=None, month=None, day=None, weeks=4):
        """
        The moving average of cycle time for every day in the last N weeks.
        """

        end_date = make_end_date(year, month, day)
        start_date = end_date - relativedelta(weeks=weeks)
        start_date = make_start_date(date=start_date)

        qs = self.done().filter(
            done_date__lte=end_date,
            done_date__gte=start_date,
        )

        try:
            average = qs.average('_cycle_time')
        except TypeError:
            average = float('nan')

        if math.isnan(average):
            return 0

        return int(round(average))

    def moving_lead_time(self, year=None, month=None, day=None, weeks=4):
        """
        The moving average of lead time for every day in the last N weeks.
        """

        end_date = make_end_date(year, month, day)
        start_date = end_date - relativedelta(weeks=weeks)
        start_date = make_start_date(date=start_date)

        qs = self.done().filter(
            done_date__lte=end_date,
            done_date__gte=start_date,
        )

        average = qs.average('_lead_time')
        if math.isnan(average):
            average = 0

        return int(round(average))

    def done(self):
        """
        Kards that have been completed.
        """
        return self.filter(done_date__exists=True)

    def done_in_month(self, year=None, month=None, day=None, date=None):
        """
        Kards that have been completed in the specified month.
        """
        if not date:
            date = munge_date(year=year, month=month, day=day)
            date = make_end_date(date=date)

        start_date, faux_end_date = month_range(date)

        results = self.done().filter(done_date__lte=date,
            done_date__gte=start_date)
        return results

class Kard(app.db.Document):
    """
    Represents a card on a Kanban board.
    """
    _ticket_system = None

    key = app.db.StringField(required=True, unique=True)
    """A unique string that matches a Kard up to a ticket in a parent system."""

    title = app.db.StringField()
    backlog_date = app.db.DateTimeField(required=True)
    """When the card entered the backlog."""

    start_date = app.db.DateTimeField()
    """When the card was started."""

    done_date = app.db.DateTimeField()
    """When the card was completed."""

    _cycle_time = app.db.IntField(db_field="cycle_time")
    _lead_time = app.db.IntField(db_field="lead_time")
    team = app.db.StringField(required=True, default="")
    """A selection from a user supplied list of teams/assignees. See :ref:`CARD_TEAMS`"""

    state = app.db.StringField(required=True, default="Unknown")
    """Which column on the kanban board the card is in."""
    priority = app.db.IntField(required=False)
    """Used when ordering cards in the backlog."""

    blocked = app.db.BooleanField(default=False)
    """Is the card currently blocked."""

    blocked_ever = app.db.BooleanField(default=False)
    """Was the card ever blocked in its history."""

    blockers = app.db.ListField(
        app.db.EmbeddedDocumentField(BlockerRecord),
    )

    created_at = app.db.DateTimeField(required=True)

    due_date = app.db.DateTimeField(required=False)
    _service_class = app.db.StringField(required=False, db_field="service_class")
    _type = app.db.StringField(required=False)
    _assignee = app.db.StringField(db_field="assignee")
    _version = app.db.StringField(required=False, db_field="version")

    _ticket_system_updated_at = app.db.DateTimeField()
    _ticket_system_data = app.db.DictField()

    meta = {
        'queryset_class': KardQuerySet,
        'collection': 'kard',
        'ordering': ['-due_date', '+priority', '-backlog_date'],
        'auto_create_index': True,
        'indexes': [('state', 'team'), ('team', 'done_date'), 'team', '_type', '_service_class', '_cycle_time', '_lead_time', 'due_date'],
    }

    EXPORT_FIELDNAMES = (
        'key',
        'title',
        'backlog_date',
        'start_date',
        'done_date',
        'state',
    )

    @property
    def service_class(self):
        if self._service_class:
            classdef = app.config.get('SERVICE_CLASSES', {}).get(
                self._service_class, {})
        else:
            classdef = app.config.get('SERVICE_CLASSES', {}).get(
                'default', {})

        service_class = {
            'name': classdef.get('name', None),
            'upper': classdef.get('upper', None),
            'lower': classdef.get('lower', None),
            'wip': classdef.get('wip', None),
        }
        return service_class


    def _convert_dates_to_datetimes(self, date):
        if not date:
            return None
        if not hasattr(date, "hour"):
            return datetime.datetime(date.year, date.month, date.day,
                23, 59, 59, 0)
        return date

    def block(self, reason, blocked_at=None):
        if not blocked_at:
            blocked_at = datetime.datetime.now()

        b = BlockerRecord(
            reason=reason,
            blocked_at=blocked_at
        )
        self.blockers.append(b)

        self.blocked = True
        self.blocked_ever = True
        return True

    def unblock(self, unblocked_at=None):
        if not unblocked_at:
            unblocked_at = datetime.datetime.now()
        self.blocked = False

        open_blockers = [b for b in self.blockers if b.unblocked_at is None]
        for b in open_blockers:
            b.unblocked_at = unblocked_at

        return True

    def _set_dates(self):
        self.backlog_date = self._convert_dates_to_datetimes(self.backlog_date)
        self.start_date = self._convert_dates_to_datetimes(self.start_date)
        self.done_date = self._convert_dates_to_datetimes(self.done_date)
        self.due_date = self._convert_dates_to_datetimes(self.due_date)

        if not self.created_at:
            self.created_at = now()

    @property
    def old_state(self):
        try:
            k = Kard.objects.only('state').get(key=self.key, )
            old_state = k.state
        except Kard.DoesNotExist:
            old_state = None
        return old_state

    @property
    def state_changing(self):
        if self.old_state != self.state:
            return True
        else:
            return False

    def _assignee_state_changes(self):
        assignee_rules = app.config.get('STATE_ASSIGNEE_RULES', {}).get(self.state, {})
        target_state = assignee_rules.get(self._assignee, None)
        if target_state:
            self.state = target_state

    def _auto_state_changes(self):
        # Auto move to done
        if self.done_date:
            states = States()
            self.in_progress = False
            self.state = states.done

        self._assignee_state_changes()

        if self.blocked:
            # Do we have a state change?
            if self.state_changing:
                self.unblock()

    def _set_cycle_lead_times(self):
        # Auto fill in final cycle and lead time
        if self.done_date and self.start_date:
            self._cycle_time = self.cycle_time
            self._lead_time = self.lead_time

    def save(self, *args, **kwargs):
        self._set_dates()

        self._set_cycle_lead_times()

        self._type = self.ticket_system.type or app.config.get('DEFAULT_TYPE', '')
        if self._type:
            self._type = self._type.strip()
        self._version = self.ticket_system.get_version()
        self._assignee = self.ticket_system_data.get('assignee', '')
        self.title = self.ticket_system_data.get('summary', '')
        self.key = self.key.upper()
        ticket_class = self.ticket_system_data.get('service_class', None)
        if ticket_class:
            self._service_class = ticket_class

        ticketdatasync.set_due_date_from_ticket(self, self.ticket_system_data)

        self._auto_state_changes()
        super(Kard, self).save(*args, **kwargs)

    @classmethod
    def update_flow_records(cls):
        if app.config.get('UPDATE_FLOW_ON_SAVE', False):
            from kardboard.tasks import update_flow_reports
            update_flow_reports.apply_async(expires=15 * 60)

    @property
    def type(self):
        # Fill in the type from the ticket helper if
        # there is one, and if not the config'd default
        return self._type or app.config.get('DEFAULT_TYPE', '')

    @classmethod
    def in_progress(klass, date=None):
        """
        Cards that are in progress as of the supplied date (or now).

        In progress is a semi-tricky calculation.
        If the date is today, it's easy, it's any
        ticket that doesn't have a done_date.
        If the date is earlier, then it's:

            a.) Any ticket without a done_date
            whose backlog_date is lte
            than the reference date **AND**

            b.) Any ticket with a done_date
            greater than the reference date
            and a start_date earlier than
            the reference date
        """
        if not date:
            return klass.objects.filter(done_date=None,
                start_date__exists=True)

        query_a = Q(done_date=None) & Q(start_date__lte=date)
        query_b = Q(done_date__gt=date) & Q(start_date__lte=date)

        results_a = list(klass.objects.filter(query_a))
        results_b = list(klass.objects.filter(query_b))

        all_ids = [c.id for c in results_a]
        all_ids = set(all_ids)
        all_ids.update([c.id for c in results_b])
        qs = klass.objects.filter(id__in=all_ids)
        return qs

    @classmethod
    def backlogged(klass, date=None):
        """
        Cards that are backlogged as of the supplied date (or now).

        Backlogged is a semi-tricky calculation.
        If the date is today, it's easy, it's any
        ticket that doesn't have a done_date or a
        start_date.

        If the date is earlier, then it's:
            a.) Any ticket without a done_date
                whose backlog_date is lte
                than the reference date and who's
                start_date is lte the reference date **AND**

            b.) Any ticket with a start_date
                greater than the reference date
                and a backlog_date earlier than
                the reference date
        """
        if not date:
            return klass.objects.filter(start_date=None)

        query_a = Q(start_date=None) & \
            Q(backlog_date__lte=date)
        query_b = Q(start_date__gt=date) & \
            Q(backlog_date__lte=date)

        results_a = list(klass.objects.filter(query_a))
        results_b = list(klass.objects.filter(query_b))

        all_ids = [c.id for c in results_a]
        all_ids = set(all_ids)
        all_ids.update([c.id for c in results_b])
        return klass.objects.filter(id__in=all_ids)

    @property
    def cycle_time(self):
        """
        Caclucation of the number of days between the start of a card
        and its completion. Returns None if the card hasn't completed yet.
        """
        if self.start_date and self.done_date:
            return days_between(self.start_date, self.done_date)

    @property
    def lead_time(self):
        """
        Caclucation of the number of days between the backlogging of a card
        and its completion. Returns None if the card hasn't completed yet.
        """
        if self.done_date:
            return days_between(self.backlog_date, self.done_date)

    def current_cycle_time(self, today=None):
        """
        Caclucation of the number of days between the start of a card
        and a comparison point (defaults to today).
        Returns None if the card hasn't started yet.
        """
        if not self.start_date:
            return None

        if today is None and self.done_date is None:
            today = now()
        elif today is None and self.done_date is not None:
            today = self.done_date
        return days_between(self.start_date, today)

    def current_lead_time(self, today=None):
        """
        Caclucation of the number of days between the backlogging of a card
        and a comparison point (defaults to today).
        """
        if not self.backlog_date:
            return None

        if today is None and self.done_date is None:
            today = now()
        elif today is None and self.done_date is not None:
            today = self.done_date
        return days_between(self.backlog_date, today)

    @property
    def cycle_goal(self):
        classdef = self.service_class
        lower = classdef.get('lower')
        upper = classdef.get('upper')
        if lower is not None and upper is not None:
            return lower, upper
        return None

    @property
    def cycle_in_goal(self):
        if self.cycle_vs_goal == 0:
            return True
        return False

    @property
    def cycle_over_goal(self):
        if self.cycle_vs_goal > 0:
            return True
        return False

    @property
    def is_card(self):
        defect_types = app.config.get('DEFECT_TYPES', [])
        if self.type in defect_types:
            return False
        return True

    @property
    def cycle_vs_goal(self):
        if not self.cycle_goal:
            return 0

        lower, upper = self.cycle_goal
        super_upper = upper * 2
        if self.done_date:
            current = self.cycle_time
        else:
            current = self.current_cycle_time()

        if current < lower:
            return -1
        elif current >= lower and current <= upper:
            return 0
        elif current >= super_upper:
            return 2
        elif current >= upper:
            return 1

    def __unicode__(self):
        backlog, start, done = self.backlog_date, self.start_date, \
            self.done_date
        priority = ""

        if backlog:
            backlog = backlog.strftime("%m/%d/%Y")
        if start:
            start = start.strftime("%m/%d/%Y")
        if done:
            done = done.strftime("%m/%d/%Y")
        if hasattr(self, 'priority') and self.priority:
            priority = "P%s | " % (self.priority, )

        return u"%s -- %s%s | %s | %s" % (self.key, priority, backlog, start, done)

    @property
    def ticket_system(self):
        """
        Instance of :ref:`TICKET_HELPER`
        """
        if self._ticket_system:
            return self._ticket_system

        helper_setting = app.config['TICKET_HELPER']
        modname = '.'.join(helper_setting.split('.')[:-1])
        klassnam = helper_setting.split('.')[-1]
        mod = importlib.import_module(modname)
        klass = getattr(mod, klassnam)

        helper = klass(app.config, self)
        self._ticket_system = helper
        return helper

    @property
    def ticket_system_data(self):
        """
        Dictionary of data supplied by :ref:`TICKET_HELPER`.

        The exact composition of the dictionary varies by the helper used.
        """
        if not self._ticket_system_data:
            return {}
        else:
            return self._ticket_system_data

    @property
    def assignee(self):
        return self._assignee
