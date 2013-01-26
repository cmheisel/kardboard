from datetime import datetime

from kardboard.tests.core import KardboardTestCase


class TicketDataSyncTests(KardboardTestCase):
    def setUp(self):
        super(TicketDataSyncTests, self).setUp()
        from kardboard.services import ticketdatasync
        self.service = ticketdatasync

    def test_due_date_changes_from_some_to_none(self):
        k = self.make_card()
        t = k.ticket_system_data
        t['due_date'] = datetime.now()

        self.service.set_due_date_from_ticket(k, t)

        self.assert_(k.due_date)

        t['due_date'] = None
        self.service.set_due_date_from_ticket(k, t)
        self.assertEqual(None, k.due_date)

    def test_due_date_gets_set(self):
        k = self.make_card()
        t = k.ticket_system_data
        t['due_date'] = datetime.now()

        self.service.set_due_date_from_ticket(k, t)
        self.assertEqual(t['due_date'], k.due_date)
