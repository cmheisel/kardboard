from dateutil.relativedelta import relativedelta

from mongoengine.queryset import Q

from kardboard.app import app
from kardboard.models.states import States
from kardboard.models.kard import Kard
from kardboard.services import teams as teams_service
from kardboard.util import (
    now,
    log_exception
)


class DisplayBoard(object):
    def __init__(self, teams=None, done_days=7):
        self.states = States()
        self.done_days = done_days
        self._cards = None
        self._rows = []

        if teams is None:
            teams = teams_service.setup_teams(app.config).names
        self.teams = teams

    def __iter__(self):
        for row in self.rows:
            yield row

    @property
    def headers(self):
        headers = [dict(state=s) for s in self.states]
        if len(self.teams) > 1:
            headers.insert(0, dict(label='Team'))

        header_counts = [0 for h in headers]
        for row in self.rows:
            for cell in row:
                index = row.index(cell)
                if cell.get('cards', None) is not None:
                    header_counts[index] += len(cell['cards'])
                else:
                    header_counts[index] = None

        for i in xrange(0, len(header_counts)):
            count = header_counts[i]
            headers[i]['count'] = count

        return tuple(headers)

    @property
    def rows(self):
        if self._rows:
            return self._rows
        rows = []
        for team in self.teams:
            row = []
            if len(self.teams) > 1:
                row.append({'label': team})
            for state in self.states:
                cards = [card for card in self.cards if card.state == state and card.team == team]
                if state in self.states.pre_start:
                    pri_cards = [c for c in cards if c.priority is not None]
                    pri_cards = sorted(pri_cards, key=lambda c: c.priority)
                    versioned = [c for c in cards if c.priority is None and c._version is not None]
                    versioned.sort(key=lambda c: c._version)
                    non_versioned = [c for c in cards if c.priority is None and c._version is None]
                    non_versioned.sort(key=lambda c: c.created_at)
                    non_versioned.reverse()

                    cards = pri_cards + versioned + non_versioned
                elif state in self.states.in_progress:
                    cards = sorted(cards, key=lambda c: c.current_cycle_time())
                    cards.reverse()
                else:
                    try:
                        cards = sorted(cards, key=lambda c: c.done_date)
                    except TypeError, e:
                        bad_cards = [c for c in cards if not c.done_date]
                        message = "The following cards have no done date: %s" % (bad_cards)
                        log_exception(e, message)
                        raise
                cell = {'cards': cards, 'state': state}
                row.append(cell)
            rows.append(row)
        self._rows = rows
        return self._rows

    @property
    def cards(self):
        if self._cards:
            return self._cards

        in_progress_q = Q(
            state__in=self.states.in_progress,
            team__in=self.teams)
        backlog_q = Q(
            state__in=self.states.pre_start,
            team__in=self.teams)
        done_q = Q(done_date__gte=now() - relativedelta(days=self.done_days),
            team__in=self.teams)
        cards_query = backlog_q | in_progress_q | done_q

        self._cards = list(
            Kard.objects.filter(cards_query).exclude('_ticket_system_data')
        )
        return self._cards
