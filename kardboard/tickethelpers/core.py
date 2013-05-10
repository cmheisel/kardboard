import datetime

class TicketHelper(object):
    def __init__(self, config, kard):
        self.app_config = config
        self.card = kard

    def get_title(self, key=None):
        """
        The title of the ticket
        """
        pass

    def get_ticket_url(self, key=None):
        """
        A URL to the ticket in the orignating system.
        """
        pass

    def update(self, sync=False):
        """
        Schedules a job to update the ticket from its originating system.

        If sync is True, then the call is executed immediately as a blocking IO task.
        """
        now = datetime.datetime.now()
        self.card._ticket_system_updated_at = now

    def actually_update(self):
        """
        Method called by the scheduled task. Updates the ticket from the originating system.
        """
        pass

    def login(self, username, password):
        """
        Method used to authenticate a user. If successfull, it returns True.
        """
        pass

    @property
    def type(self):
        return self.get_type()

    def get_type(self):
        """
        Method called to extract, if any, the ticket type from the upstream ticket system.
        For example: Bug, Feature, Improvement, etc.
        """
        pass

    def get_version(self):
        """
        Method called to extract, if any, the version from the upstream ticket system.
        """
        pass
