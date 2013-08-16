from kardboard.app import app
from kardboard.util import slugify


class State(object):
    def __init__(self, name, buffer, is_buffer):
        self.name = name
        self.buffer = buffer
        self.is_buffer = is_buffer

    def __unicode__(self):
        return unicode(self.name)

    def __str__(self):
        return str(self.name)


class States(object):
    def __init__(self, config=None):
        if not config:
            config = app.config
        self.config = config
        self.states = self._parse_state_config(config.get('CARD_STATES', ()))
        self.state_names = [s.name for s in self.states]
        self.backlog_state = self._find_backlog()
        self.start_state = self._find_start()
        self.done_state = self._find_done()
        self.pre_start = self._find_pre_start()
        self.in_progress = self._find_in_progress()

        self.backlog = self.backlog_state.name
        self.start = self.start_state.name
        self.done = self.done_state.name

    def _parse_state_config(self, config):
        states = []
        for item in config:
            if isinstance(item, tuple):
                s = State(
                    name=item[0],
                    buffer=item[1],
                    is_buffer=False,
                )
                sb = State(
                    name=item[1],
                    buffer=None,
                    is_buffer=True
                )
                states.append(s)
                states.append(sb)
            else:
                s = State(
                    name=item,
                    buffer=None,
                    is_buffer=False,
                )
                states.append(s)
        return states

    def _find_pre_start(self):
        """
        Find all states, in order, that come
        before a start_date is applied.
        """
        return [s.name for s in self.states if self.states.index(s) < self.states.index(self.start_state)]

    def _find_in_progress(self):
        """
        Find all states, in order, that come after after backlog
        but before done.
        """
        in_progress = [s.name for s in self.states
            if self.states.index(s) > self.states.index(self.backlog_state) and
            self.states.index(s) < self.states.index(self.done_state)]
        return in_progress

    def _find_done(self):
        default = -1
        done = self.config.get('DONE_STATE', default)
        return self.states[done]

    def _find_start(self):
        default = 1
        start = self.config.get('START_STATE', default)
        return self.states[start]

    def _find_backlog(self):
        default = 0
        backlog = self.config.get('BACKLOG_STATE', default)
        return self.states[backlog]

    def __iter__(self):
        for state in self.states:
            yield state.name

    def __unicode__(self):
        return unicode([unicode(s) for s in self])

    def __str__(self):
        return str([str(s) for s in self])

    def __getitem__(self, key):
        return self.states[key].name

    def index(self, arg):
        """
        The index method routes requests for strings
        differently than requests for the new in 1.12 State objects.
        """
        if isinstance(arg, (str, unicode)):
            return self.state_names.index(arg)
        else:
            return self.states.index(arg)

    def find_by_slug(self, slug):
        by_slug = {}
        for state in self:
            by_slug[slugify(state)] = state
        return by_slug[slug]

    @property
    def orderable(self):
        orderable = [self._find_backlog().name, ]
        for state in self.config.get('FUNNEL_VIEWS', {}).keys():
            if state in list(self):
                orderable.append(state)
        return list(set(orderable))

    @property
    def for_forms(self):
        form_list = [('', ''), ]  # Add a blank
        form_list.extend([(state.name, state.name) for state in self.states])
        return tuple(form_list)

    @property
    def active(self):
        active = []
        for state in self.states:
            if state.is_buffer is False:
                active.append(state)
        return active
