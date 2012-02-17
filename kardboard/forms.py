
#import datetime

from wtforms import Form, TextField, SelectField, IntegerField, PasswordField, validators, ValidationError
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

STATE_CHOICES = (
    ('Todo', 'Todo'),
    ('Doing', 'Doing'),
    ('Done', 'Done'),
)

TEAM_CHOICES = (
    ('Team 1', 'Team 1'),
    ('Team 2', 'Team 2'),
)


class CardForm(Form):
    key = TextField(u'JIRA Key',
        validators=[validators.required()])
    title = TextField(u'Card title',
        validators=[validators.required()])
    team = SelectField(u'Team', choices=TEAM_CHOICES,
        validators=[validators.required()])
    state = SelectField(u'State', choices=STATE_CHOICES,
        validators=[validators.required()])
    backlog_date = DateField(u'Backlog date', display_format="%m/%d/%Y",
        validators=[validators.required()])
    start_date = DateField(u'Start date', display_format="%m/%d/%Y",
        validators=[validators.optional()])
    done_date = DateField(u'Done date', display_format="%m/%d/%Y",
        validators=[validators.optional()])
    priority = IntegerField(u'Ordering', validators=[validators.optional()])

    def populate_obj(self, obj):
        super(CardForm, self).populate_obj(obj)
        if self.data['priority'] == u"":
            obj.priority = None


class CardBlockForm(Form):
    reason = TextField(u'Reason',
        validators=[validators.required()])
    blocked_at = DateField(u'Blocked starting', display_format="%m/%d/%Y",
        validators=[validators.required()])


class CardUnblockForm(Form):
    unblocked_at = DateField(u'Unblocked date', display_format="%m/%d/%Y",
        validators=[validators.required()])


def get_card_form(new=False):
    if new:
        CardForm.validate_key = Unique(Kard, 'key')
    else:
        if hasattr(CardForm, 'validate_key'):
            delattr(CardForm, 'validate_key')
    return CardForm


class LoginForm(Form):
    username = TextField(u'Username',
        validators=[validators.required()])
    password = PasswordField(u'Password',
        validators=[validators.required()])
