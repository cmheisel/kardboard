from .core import ViewTestCase, KardboardTestCase


class SimpleTest(KardboardTestCase):
    def test_sanity(self):
        assert True


class ViewTests(ViewTestCase):
    def test_my_view(self):
        from ..views import my_view
        request = self.testing.DummyRequest()
        info = my_view(request)
        self.assertEqual(info['project'], 'kardboard')
