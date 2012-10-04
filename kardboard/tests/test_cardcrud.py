import copy
import datetime

from kardboard.tests.core import KardboardTestCase


class CardBlockTests(KardboardTestCase):
    def setUp(self):
        super(CardBlockTests, self).setUp()
        self.card = self.make_card()
        self.card.save()
        self.required_data = {
            'reason': 'You gotta lock that down',
            'blocked_at': '06/11/1911',
        }
        self.config['TICKET_HELPER'] = \
            'kardboard.tickethelpers.TestTicketHelper'

    def tearDown(self):
        self.card.delete()

    def _get_target_url(self, card=None):
        if not card:
            card = self.card.key
        return '/card/%s/block/' % (card, )

    def _get_target_class(self):
        return self._get_card_class()

    def test_blocking(self):
        res = self.app.get(self._get_target_url())
        self.assertEqual(200, res.status_code)
        self.assertIn('<form', res.data)
        self.assertIn(self.card.key, res.data)
        self.assertIn(self.card.title, res.data)

    def test_blocking_post(self):
        self.assertEqual(False, self.card.blocked)
        res = self.app.post(self._get_target_url(),
            data=self.required_data)
        self.assertEqual(302, res.status_code)
        self.card.reload()
        self.assertEqual(True, self.card.blocked)
        self.assertEqual(1, len(self.card.blockers))
        self.assertEqual(True, self.card.blocked_ever)

    def test_blocking_not_found(self):
        url = self._get_target_url("CMS-404")
        res = self.app.get(url)
        self.assertEqual(404, res.status_code)

    def test_blocking_cancel(self):
        self.assertEqual(False, self.card.blocked)
        res = self.app.post(self._get_target_url(),
            data={'cancel': "Cancel"})
        self.assertEqual(302, res.status_code)
        self.card.reload()
        self.assertEqual(False, self.card.blocked)


class CardUnblockTests(KardboardTestCase):
    def setUp(self):
        super(CardUnblockTests, self).setUp()
        self.blocked_at = datetime.datetime(
            2011, 6, 12)
        self.card = self.make_card()
        self.card.block("Foo", self.blocked_at)
        self.card.save()
        self.required_data = {
            'unblocked_at': '06/13/2011',
        }
        self.config['TICKET_HELPER'] = \
            'kardboard.tickethelpers.TestTicketHelper'

    def tearDown(self):
        self.card.delete()

    def _get_target_url(self, card=None):
        if not card:
            card = self.card.key
        return '/card/%s/block/' % (card, )

    def _get_target_class(self):
        return self._get_card_class()

    def test_unblocking(self):
        res = self.app.get(self._get_target_url())
        self.assertEqual(200, res.status_code)
        self.assertIn('<form', res.data)
        self.assertIn(self.card.key, res.data)
        self.assertIn(self.card.title, res.data)

    def test_unblocking_post(self):
        self.assertEqual(True, self.card.blocked)
        res = self.app.post(self._get_target_url(),
            data=self.required_data)
        self.assertEqual(302, res.status_code)
        self.card.reload()
        self.assertEqual(False, self.card.blocked)
        self.assertEqual(True, self.card.blocked_ever)
        self.assertEqual(1, len(self.card.blockers))

    def test_unblocking_cancel(self):
        self.assertEqual(True, self.card.blocked)
        res = self.app.post(self._get_target_url(),
            data={'cancel': "Cancel"})
        self.assertEqual(302, res.status_code)
        self.card.reload()
        self.assertEqual(True, self.card.blocked)


class CardCRUDTests(KardboardTestCase):
    def setUp(self):
        super(CardCRUDTests, self).setUp()
        self.required_data = {
            'key': u'CMSIF-199',
            'title': u'You gotta lock that down',
            'backlog_date': u"06/11/1911",
            'state': u'Todo',
            'team': u'Team 1',
        }
        self.config['TICKET_HELPER'] = \
            'kardboard.tickethelpers.TestTicketHelper'
        self.flask_app.config['TICKET_AUTH'] = True
        self.login()

    def tearDown(self):
        super(CardCRUDTests, self).tearDown()
        self.flask_app.config['TICKET_AUTH'] = False
        self.logout()

    def _get_target_url(self):
        return '/card/add/'

    def _get_target_class(self):
        return self._get_card_class()

    def test_add_card(self):
        klass = self._get_target_class()

        res = self.app.get(self._get_target_url())
        self.assertEqual(200, res.status_code)
        self.assertIn('<form', res.data)

        res = self.app.post(self._get_target_url(),
            data=self.required_data)

        self.assertEqual(302, res.status_code)
        self.assertEqual(1, klass.objects.count())

        k = klass.objects.get(key=self.required_data['key'])
        self.assert_(k.id)

    def test_add_card_with_qs_params(self):
        key = "CMSCMS-127"
        url = "%s?key=%s" % (self._get_target_url(), key)
        res = self.app.get(url)
        self.assertEqual(200, res.status_code)
        self.assertIn('<form', res.data)
        self.assertIn('value="%s"' % (key, ), res.data)

    def test_add_card_with_no_title(self):
        klass = self._get_target_class()

        data = copy.copy(self.required_data)
        del data['title']

        res = self.app.post(self._get_target_url(),
            data=data)

        self.assertEqual(302, res.status_code)
        self.assertEqual(1, klass.objects.count())

        # This should work because we mocked TestHelper
        # in setUp
        k = klass.objects.get(key=self.required_data['key'])
        self.assert_(k.id)
        self.assertEqual(k.title, "Dummy Title from Dummy Ticket System")

    def test_add_duplicate_card(self):
        klass = self._get_target_class()
        card = klass(**self.required_data)
        card.backlog_date = datetime.datetime.now()
        card.save()

        res = self.app.get(self._get_target_url())
        self.assertEqual(200, res.status_code)
        self.assertIn('<form', res.data)

        res = self.app.post(self._get_target_url(),
            data=self.required_data)

        self.assertEqual(200, res.status_code)

    def test_card_with_and_without_priority(self):
        klass = self._get_target_class()

        card = klass(**self.required_data)
        card.backlog_date = datetime.datetime.now()
        card.priority = 2
        card.save()

        self.required_data['priority'] = u""

        target_url = "/card/%s/edit/" % (card.key, )
        self.app.post(target_url,
            data=self.required_data)

        k = klass.objects.get(key=self.required_data['key'])
        self.assert_(k.id)
        self.assertEqual(k.priority, None)

    def test_edit_card(self):
        klass = self._get_target_class()

        card = klass(**self.required_data)
        card.backlog_date = datetime.datetime.now()
        card.save()

        target_url = "/card/%s/edit/" % (card.key, )
        res = self.app.get(target_url)
        self.assertEqual(200, res.status_code)
        self.assertIn(card.key, res.data)
        self.assertIn(card.title, res.data)

        res = self.app.post(target_url,
            data=self.required_data)

        k = klass.objects.get(key=self.required_data['key'])
        self.assert_(k.id)
        self.assertEqual(302, res.status_code)
        self.assertEqual(1, klass.objects.count())
        self.assertEqual(6, k.backlog_date.month)
        self.assertEqual(11, k.backlog_date.day)
        self.assertEqual(1911, k.backlog_date.year)

    def test_edit_card_and_redirects(self):
        klass = self._get_target_class()

        card = klass(**self.required_data)
        card.backlog_date = datetime.datetime.now()
        card.save()

        target_url = "/card/%s/edit/?next=%%2Fcard%%2F%s%%2F" % (card.key, card.key)

        res = self.app.get(target_url)
        action_url = 'action="http://localhost%s"' % target_url
        self.assertIn(action_url, res.data)

        res = self.app.post(target_url,
            data=self.required_data)

        k = klass.objects.get(key=self.required_data['key'])
        self.assertEqual(302, res.status_code)
        self.assertEqual('http://localhost/card/%s/' % card.key, res.location)


    def test_delete_card(self):
        klass = self._get_target_class()

        card = klass(**self.required_data)
        card.backlog_date = datetime.datetime.now()
        card.save()

        target_url = "/card/%s/delete/" % (card.key, )
        res = self.app.get(target_url)
        self.assertEqual(200, res.status_code)
        self.assertIn('value="Cancel"', res.data)
        self.assertIn('value="Delete"', res.data)
        self.assert_(klass.objects.get(key=card.key))

        res = self.app.post(target_url, data={'cancel': 'Cancel'})
        self.assertEqual(302, res.status_code)
        self.assert_(klass.objects.get(key=card.key))

        res = self.app.post(target_url, data={'delete': 'Delete'})
        self.assertEqual(302, res.status_code)

    def login(self):
        login_data = {'username': 'username', 'password': 'password'}
        self.app.post('/login/', data=login_data)

    def logout(self):
        self.app.get('/logout/')
