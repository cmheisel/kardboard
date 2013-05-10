from core import TicketHelper


class NullHelper(TicketHelper):
    def get_title(self, key=None):
        return ''

    def get_ticket_url(self, key=None):
        return ''

    def update(self, sync=False):
        super(NullHelper, self).update(sync)
        test_data = {}
        if self.card._service_class:
            test_data['service_class'] = self.card._service_class
        self.card._ticket_system_data = test_data
        return None

    def actually_update(self):
        return None

    def login(self, username, password):
        return None
