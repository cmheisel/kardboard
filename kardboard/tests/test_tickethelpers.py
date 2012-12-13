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
        self.assert_(k._ticket_system_data != {})
        self.assert_(k._ticket_system_updated_at is not None)

        k.ticket_system.update()
        k.reload()
        now = datetime.datetime.now()
        updated_at = k._ticket_system_updated_at
        diff = now - updated_at
        self.assert_(diff.seconds <= 1)

    def test_version(self):
        k = self.card
        actual = k.ticket_system.get_version()
        self.assertEqual("1.2.1", actual)
        k.save()
        self.assertEqual(k._version, "1.2.1")

    def test_people(self):
        k = self.card
        k.save()

        k.ticket_system.update()
        k.reload()

        self.assert_(k.ticket_system_data['reporter'] == 'cheisel')

        self.assert_(len(k.ticket_system_data['developers']) > 0)
        self.assert_(len(k.ticket_system_data['testers']) > 0)

    def test_get_title(self):
        h = self._make_one()
        expected = self.ticket.summary
        actual = h.get_title()
        self.assertEqual(expected, actual)

    def test_get_type(self):
        h = self._make_one()
        expected = "New Feature"
        self.assertEqual(expected, h.get_type())

    def test_get_service_class(self):
        h = self._make_one()
        expected = "2 - Fixed Date"
        self.assertEqual(expected, h.get_service_class())

    def test_get_due_date(self):
        h = self._make_one()
        expected = datetime.datetime(
            2012, 12, 17, 10, 10, 00
        )
        self.assertEqual(expected, h.get_due_date())

    def test_get_ticket_url(self):
        h = self._make_one()
        expected = "%s/browse/%s" % (self.config['JIRA_WSDL'],
            self.card.key)
        actual = h.get_ticket_url()
        self.assertEqual(actual, expected)

    def test_limited_people(self):
        from kardboard.tests.mocks import MockJIRAIssueWithOnlyUIDevs

        k = self.card
        devs = k.ticket_system.id_devs(MockJIRAIssueWithOnlyUIDevs())
        assert len(devs) == 0
