from datetime import datetime

import unittest2

from kardboard.tests.mocks import Mock


class TicketDataSyncTests(unittest2.TestCase):
    def setUp(self):
        super(TicketDataSyncTests, self).setUp()
        from kardboard.services import ticketdatasync
        self.service = ticketdatasync

    def test_due_date_changes_from_some_to_none(self):
        kard = Mock()
        kard.due_date = datetime.now()

        ticket_data = {'due_date': None}
        self.service.set_due_date_from_ticket(kard, ticket_data)
        self.assertEqual(None, kard.due_date)

    def test_due_date_gets_set(self):
        kard = Mock()
        ticket_data = {}
        ticket_data['due_date'] = datetime.now()

        self.service.set_due_date_from_ticket(kard, ticket_data)
        self.assertEqual(ticket_data['due_date'], kard.due_date)
