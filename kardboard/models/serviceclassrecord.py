from kardboard.app import app
from kardboard.util import (
    now,
    make_end_date,
    make_start_date,
    average,
)


def report_on_cards(cards):
    data = {}
    for k in cards:
        class_cards = data.get(k.service_class.get('name'), [])
        class_cards.append(k)
        data[k.service_class.get('name')] = class_cards

    total = sum([len(v) for k, v in data.items()])

    report = {}
    for classname, cards in data.items():
        sclass = cards[0].service_class
        cycle_time_average = int(round(average(
            [c.current_cycle_time() for c in cards])))
        cards_hit_goal = len([c.key for c in cards
            if c.current_cycle_time() <= sclass.get('upper')])

        report[classname] = {
            'service_class': sclass.get('name'),
            'wip': len(cards),
            'wip_percent': len(cards) / float(total),
            'cycle_time_average': cycle_time_average,
            'cards_hit_goal': cards_hit_goal,
            'cards_hit_goal_percent': cards_hit_goal / float(len(cards)),
        }

    return report


class ServiceClassSnapshot(app.db.Document):
    """
    A snapshot of service class metadata, per group.
    """
    group = app.db.StringField(required=True, default="all", unique=True)
    """The report group to which this daily report belongs."""

    updated_at = app.db.DateTimeField(required=True)
    """The datetime the record was last updated at."""

    data = app.db.DictField(required=False, default={})
    """The report on service classes."""

    meta = {
        'allow_inheritance': True,
    }

    @classmethod
    def calculate(cls, group="all"):
        from kardboard.models import Kard
        from kardboard.models import ReportGroup

        try:
            record = cls.objects.get(
                group=group,
            )
        except cls.DoesNotExist:
            record = cls()
            record.group = group
            record.data = {}

        kards = ReportGroup(group, Kard.in_progress())
        record.data = report_on_cards(list(kards.queryset))
        record.save()
        return record

    def save(self, *args, **kwargs):
        self.updated_at = now()
        super(ServiceClassSnapshot, self).save(*args, **kwargs)


class ServiceClassRecord(app.db.Document):
    """
    A snapshot of service class metadata, per group,
    within a start and end date.
    """
    start_date = app.db.DateTimeField(required=False,
        unique_with=['group', 'end_date'])
    """The start date for the records"""

    end_date = app.db.DateTimeField(required=False,
        unique_with=['group', 'start_date'])
    """The start date for the records"""

    group = app.db.StringField(required=True, default="all",
        unique_with=['start_date', 'end_date'])
    """The report group to which this daily report belongs."""

    updated_at = app.db.DateTimeField(required=True)
    """The datetime the record was last updated at."""

    data = app.db.DictField(required=False, default={})
    """The report on service classes."""

    def save(self, *args, **kwargs):
        self.updated_at = now()
        super(ServiceClassRecord, self).save(*args, **kwargs)

    @classmethod
    def calculate(cls, start_date, end_date, group="all"):
        from kardboard.models import Kard
        from kardboard.models import ReportGroup

        start_date = make_start_date(date=start_date)
        end_date = make_end_date(date=end_date)

        try:
            record = cls.objects.get(
                group=group,
                start_date=start_date,
                end_date=end_date,
            )
        except cls.DoesNotExist:
            record = cls()
            record.start_date = start_date
            record.end_date = end_date
            record.group = group
            record.data = {}

        kards = ReportGroup(group,
            Kard.objects.filter(
                done_date__gte=start_date,
                done_date__lte=end_date,
            )
        )
        record.data = report_on_cards(list(kards.queryset))
        record.save()
        return record
