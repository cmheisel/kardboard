from kardboard.app import app
from kardboard.util import slugify

class States(object):
    def __init__(self, config=None):
        if not config:
            config = app.config
        self.config = config
        self.states = config.get('CARD_STATES', ())
        self.backlog = self._find_backlog()
        self.start = self._find_start()
        self.done = self._find_done()
        self.pre_start = self._find_pre_start()
        self.in_progress = self._find_in_progress()

    def _find_pre_start(self):
        """
        Find all states, in order, that come
        before a start_date is applied.
        """
        return [s for s in self.states if self.states.index(s) < self.states.index(self.start)]

    def _find_in_progress(self):
        """
        Find all states, in order, that come after after backlog
        but before done.
        """
        in_progress = [s for s in self.states
            if self.states.index(s) > self.states.index(self.backlog) and
            self.states.index(s) < self.states.index(self.done)]
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
            yield state

    def __unicode__(self):
        return unicode(self.states)

    def __str__(self):
        return str(self.states)

    def __getitem__(self, key):
        return self.states[key]

    def index(self, *args, **kwargs):
        return self.states.index(*args, **kwargs)

    def find_by_slug(self, slug):
        by_slug = {}
        for state in self:
            by_slug[slugify(state)] = state
        return by_slug[slug]

    @property
    def for_forms(self):
        form_list = [('', ''), ]  # Add a blank
        form_list.extend([(state, state) for state in self.states])
        return tuple(form_list)
