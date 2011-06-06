
import datetime

from wtforms import Form, TextField, SelectField, validators, ValidationError
from wtforms.ext.dateutil.fields import DateField

from kardboard.models import Kard


def _make_choice_field_ready(choice_list):
    choices = [(choice, choice) for choice in choice_list]
    return tuple(choices)


class Unique(object):
    """Validator that checks for uniqueness"""
    def __init__(self, klass, field, message=None):
        self.klass = klass
        self.field = field
        if not message:
            message = u"this value must be unique"
        self.message = message

    def __call__(self, form, field):
        check = field.data.strip() in self.klass.objects.distinct(self.field)
        if check:
            raise ValidationError(self.message)

CATEGORY_CHOICES = ('Uncategorized', 'Uncategorized')


class CardDateField(DateField):
    """
    Exactly like a DateField, except it coerces into a datetime
    object since that's what the Model needs.
    """
    def process_data(self, value):
        self.data = None
        if value:
            super(CardDateField, self).process_formdata([value, ])
        if self.data and hasattr(self.data, "year"):
            year, month, day = self.data.year, self.data.month, self.data.day
            self.data = datetime.datetime(year, month, day, 23, 59, 59, 0)


    def process_formdata(self, valuelist):
        self.data = None
        if valuelist:
            super(CardDateField, self).process_formdata(valuelist)
        if self.data and hasattr(self.data, "year"):
            year, month, day = self.data.year, self.data.month, self.data.day
            self.data = datetime.datetime(year, month, day, 23, 59, 59, 0)

class CardForm(Form):
    key = TextField(u'JIRA Key',
        validators=[validators.required(), Unique(Kard, "key")])
    title = TextField(u'Card title',
        validators=[validators.required()])
    backlog_date = CardDateField(u'Backlog date', display_format="%m/%d/%Y",
        validators=[validators.required()])
    start_date = CardDateField(u'Start date', display_format="%m/%d/%Y",
        validators=[validators.optional()])
    done_date = CardDateField(u'Done date', display_format="%m/%d/%Y",
        validators=[validators.optional()])
    category = SelectField(u'Category', choices=CATEGORY_CHOICES,
        validators=[validators.optional()])
