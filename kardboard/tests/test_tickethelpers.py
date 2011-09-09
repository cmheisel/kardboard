import datetime

from mock import patch

from kardboard.tests.core import KardboardTestCase
from kardboard.tests.mocks import MockJIRAClient, MockJIRAIssue


class JIRAHelperTests(KardboardTestCase):
    def setUp(self):
        super(JIRAHelperTests, self).setUp()
        self.card = self.make_card()
        self.config['JIRA_WSDL'] = 'http://jira.example.com'
        self.config['JIRA_CREDENTIALS'] = ('foo', 'bar')
        self.config['TICKET_HELPER'] = 'kardboard.tickethelpers.JIRAHelper'
        self.ticket = MockJIRAIssue()
        self.sudspatch = patch('suds.client.Client', MockJIRAClient)
        self.sudspatch.start()

    def tearDown(self):
        super(JIRAHelperTests, self).tearDown()
        self.sudspatch.stop()
        del self.config['JIRA_WSDL']

    def _get_target_class(self):
        from kardboard.tickethelpers import JIRAHelper
        return JIRAHelper

    def _make_one(self):
        klass = self._get_target_class()
        return klass(self.config, self.card)

    def test_update(self):
        k = self.card
        k.save()
        self.assert_(k._ticket_system_data == {})
        self.assert_(k._ticket_system_updated_at is None)

        k.ticket_system.update()
        k.reload()
        now = datetime.datetime.now()
        updated_at = k._ticket_system_updated_at
        diff = now - updated_at
        self.assert_(diff.seconds <= 1)

    def test_get_title(self):
        h = self._make_one()
        expected = self.ticket.summary
        actual = h.get_title()
        self.assertEqual(expected, actual)

    def test_get_ticket_url(self):
        h = self._make_one()
        expected = "%s/browse/%s" % (self.config['JIRA_WSDL'],
            self.card.key)
        actual = h.get_ticket_url()
        self.assertEqual(actual, expected)
