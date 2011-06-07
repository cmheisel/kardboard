
#import datetime

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

CATEGORY_CHOICES = (
    ('Bug', 'Bug'),
    ('Feature', 'Feature'),
    ('Improvement', 'Improvement'),
)


class CardForm(Form):
    key = TextField(u'JIRA Key',
        validators=[validators.required()])
    title = TextField(u'Card title',
        validators=[validators.required()])
    backlog_date = DateField(u'Backlog date', display_format="%m/%d/%Y",
        validators=[validators.required()])
    start_date = DateField(u'Start date', display_format="%m/%d/%Y",
        validators=[validators.optional()])
    done_date = DateField(u'Done date', display_format="%m/%d/%Y",
        validators=[validators.optional()])
    category = SelectField(u'Category', choices=CATEGORY_CHOICES,
        validators=[validators.optional()])


class NewCardForm(CardForm):
    key = TextField(u'JIRA Key',
        validators=[validators.required(), Unique(Kard, "key")])
