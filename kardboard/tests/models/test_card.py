from ..core import ModelTestCase


class CardTests(ModelTestCase):
    def _get_class(self):
        from ...models.card import Card
        return Card

    def make_one(self, **kwargs):
        key = self.make_unique_key()
        values = {
            'title': 'Default title',
            'key': 'DEFAULT-%s' % key,
            'teams': ['Team 1', 'Team 2', ]
        }
        values.update(kwargs)
        return super(CardTests, self).make_one(**values)

    def test_make_one(self):
        c = self.make_one()
        c.save()

        assert c.id
