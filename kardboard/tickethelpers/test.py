from core import TicketHelper


class TestTicketHelper(TicketHelper):
    def get_title(self, key=None):
        title = ''
        if self.card._ticket_system_data:
            title = self.card._ticket_system_data.get('summary', '')
        else:
            self.card.ticket_system.update(sync=True)
            title = self.card.ticket_system_data.get('summary', '')
        return title

    def get_ticket_url(self):
        return u"""http://example.com/ticket/%s""" % self.card.key

    def update(self, sync=False):
        super(TestTicketHelper, self).update()
        test_data = {
            'summary': u"""Dummy Title from Dummy Ticket System""",
        }
        if self.card._service_class:
            test_data['service_class'] = self.card._service_class
        self.card._ticket_system_data = test_data

    def login(self, username, password):
        return True

    def get_version(self):
        if self.card:
            return self.card._version
        else:
            return None
