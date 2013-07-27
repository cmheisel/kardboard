from kardboard.tests.core import KardboardTestCase


class NewKardTests(KardboardTestCase):

    def _get_target_class(self):
        from kardboard.models.kard import Kard
        return Kard

    def test_worked_on_returns_assingee_if_present(self):
        k = self._get_target_class()()
        k._assignee = "cheisel"

        expected = ['cheisel', ]
        assert k.worked_on == expected

    def test_worked_on_returns_developers_present(self):
        k = self._get_target_class()()
        k._assignee = "cheisel"
        k._ticket_system_data = {
            'developers': [
                'starbuck',
                'apollo',
            ]
        }

        expected = ['cheisel', 'starbuck', 'apollo']
        assert k.worked_on == expected

    def test_worked_on_returns_testers_present(self):
        k = self._get_target_class()()
        k._assignee = "cheisel"
        k._ticket_system_data = {
            'qaers': [
                'chief',
                'gaeda',
            ]
        }

        expected = ['cheisel', 'chief', 'gaeda']
        assert k.worked_on == expected

    def test_worked_on_returns_all_present(self):
        k = self._get_target_class()()
        k._assignee = "cheisel"
        k._ticket_system_data = {
            'developers': [
                'starbuck',
                'apollo',
            ],
            'qaers': [
                'chief',
                'gaeda',
            ]
        }

        expected = ['cheisel', 'chief', 'gaeda', 'starbuck', 'apollo']
        assert k.worked_on == expected
