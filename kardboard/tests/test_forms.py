import datetime

from kardboard.tests.core import FormTests


class BlockFormTest(FormTests):
    def setUp(self):
        super(BlockFormTest, self).setUp()
        self.Form = self._get_target_class()
        self.required_data = {
            'reason': u'You gotta lock that down',
            'blocked_at': u"06/11/2011",
        }
        self.post_data = self._make_post_data(self.required_data)

    def _make_post_data(self, data):
        from werkzeug.datastructures import MultiDict
        return MultiDict(data)

    def _get_target_class(self):
        from kardboard.forms import CardBlockForm
        return CardBlockForm

    def test_form(self):
        f = self.Form(self.post_data)
        f.validate()
        self.assertEquals(0, len(f.errors))

    def test_datetime_coercing(self):
        f = self.Form(self.post_data)
        data = f.blocked_at.data
        self.assertEquals(6, data.month)


class CardFormTest(FormTests):
    def setUp(self):
        from werkzeug.datastructures import MultiDict
        super(CardFormTest, self).setUp()

        self.config['CARD_STATES'] = [
            'Todo',
            'Doing',
            'Done',
        ]

        self.config['CARD_TEAMS'] = [
            'Team 1',
            'Team 2',
        ]
        self.Form = self._get_target_class()
        self.required_data = {
            'key': u'CMSIF-199',
            'title': u'You gotta lock that down',
            'backlog_date': u"06/11/2011",
            'state': u'Doing',
            'team': u'Team 1',
        }
        self.post_data = MultiDict(self.required_data)

    def _get_target_class(self, new=True):
        from kardboard.forms import get_card_form
        return get_card_form(new=new)

    def _test_form(self, post_data, new=True):
        f = self._get_target_class(new)(post_data)
        f.validate()
        self.assertEquals(0, len(f.errors))

        card = self._get_card_class()()
        f.populate_obj(card)
        card.save()

        for key, value in self.post_data.items():
            self.assertNotEqual(
                None,
                getattr(card, key, None))
        return card

    def test_fields(self):
        self.optional_data = {
            'start_date': u'06/11/2011',
            'done_date': u'06/12/2011',
            'priority': u'2',
        }
        self.post_data.update(self.optional_data)
        self._test_form(self.post_data)

    def test_no_priority(self):
        self.optional_data = {
            'start_date': u'06/11/2011',
            'done_date': u'06/12/2011',
            'priority': u'2',
        }
        self.post_data.update(self.optional_data)

        f = self._get_target_class()(self.post_data)
        f.validate()
        self.assertEquals(0, len(f.errors))
        card = self._get_card_class()()
        f.populate_obj(card)
        card.save()
        self.assertEqual(2, card.priority)

        self.post_data['priority'] = u''
        f = self._get_target_class(new=False)(self.post_data)
        f.validate()
        f.populate_obj(card)
        card.save()
        self.assertEqual(None, card.priority)

    def test_datetime_coercing(self):
        f = self.Form(self.post_data)
        data = f.backlog_date.data
        self.assertEqual(6, data.month)

    def test_key_uniqueness(self):
        klass = self._get_card_class()
        c = klass(**self.required_data)
        c.backlog_date = datetime.datetime.now()
        c.save()

        f = self.Form(self.post_data)
        f.validate()
        self.assertIn('key', f.errors.keys())
