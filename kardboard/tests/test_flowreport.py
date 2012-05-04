from core import KardboardTestCase


class FlowReportTestCase(KardboardTestCase):

    def setUp(self):
        from kardboard.models import States
        super(FlowReportTestCase, self).setUp()
        self.states = States()
        self._set_up_cards()

    def _set_up_cards(self):
        backlog_date = self._date('start', days=-10)
        start_date = self._date('start', days=-5)
        done_date = self._date('end')

        self.teams = self.config.get('CARD_TEAMS')
        team1 = self.teams[0]
        team2 = self.teams[1]

        for team in (team1, team2):
            for i in xrange(0, 1):
                c = self.make_card(
                    backlog_date=backlog_date,
                    team=team,
                    state=self.states.backlog,
                )
                c.save()

                c = self.make_card(
                    backlog_date=backlog_date,
                    start_date=start_date,
                    team=team,
                    state=self.states.start,
                )
                c.save()

                c = self.make_card(
                    backlog_date=backlog_date,
                    start_date=start_date,
                    done_date=done_date,
                    team=team,
                    state=self.states.done,
                )
                c.save()
                c = self.make_card(
                    backlog_date=backlog_date,
                    start_date=start_date,
                    done_date=done_date,
                    team=team,
                    state=self.states.done,
                )
                c.save()

    def _get_target_class(self):
        from kardboard.models import FlowReport
        return FlowReport

    def test_group_flow_report(self):
        expected = [
            {
                'name': self.states.backlog,
                'count': 1,
            },
            {
                'name': self.states.start,
                'count': 1,
            },
            {
                'name': self.states.done,
                'count': 2,
            }
        ]
        self.test_flow_report("team-1", expected)

    def test_flow_report(self, group=None, expected=None):
        Report = self._get_target_class()
        if group == None:
            group == all
        r = Report.capture(group)

        if expected == None:
            expected = [
                {
                    'name': self.states.backlog,
                    'count': 2,
                },
                {
                    'name': self.states.start,
                    'count': 2,
                },
                {
                    'name': self.states.done,
                    'count': 4,
                }
            ]
        assert expected == r.data
