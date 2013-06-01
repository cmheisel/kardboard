import mock
import pytest
import unittest2


@pytest.mark.funnel
class FunnelTests(unittest2.TestCase):
    def _get_class(self):
        from kardboard.services.funnel import Funnel
        return Funnel

    def test_funnel_state(self):
        config = {
            'Build to OTIS': {
            }
        }
        f = self._get_class()('Build to OTIS', config['Build to OTIS'])

        assert f.state == "Build to OTIS"

    def test_funnel_throughput(self):
        config = {
            'Build to OTIS': {
                'throughput': 2,
            }
        }
        f = self._get_class()('Build to OTIS', config['Build to OTIS'])

        assert 2 == f.throughput

    def test_funnel_no_throughput(self):
        config = {
            'Build to OTIS': {
            }
        }
        f = self._get_class()('Build to OTIS', config['Build to OTIS'])

        assert f.throughput is None

    def test_find_cards(self):
        with mock.patch('kardboard.services.funnel.Kard') as mock_Kard:
            f = self._get_class()('Build to OTIS', {})
            mock_Kard.objects.filter.return_value.exclude.return_value = []
            result = f.find_cards()
            mock_Kard.objects.filter.assert_called_with(
                state="Build to OTIS",
            )
            mock_Kard.objects.filter.return_value.exclude.assert_called_with(
                '_ticket_system_data',
            )
            assert result == []

    def test_state_duration(self):
        with mock.patch('kardboard.services.funnel.StateLog') as mock_StateLog:
            f = self._get_class()('Build to OTIS', {})

            card = mock.Mock()
            fake_statelog = mock.Mock()
            fake_statelog.duration = 20
            mock_StateLog.objects.filter.return_value.order_by.return_value = [fake_statelog, ]
            duration = f.state_duration(card)
            mock_StateLog.objects.filter.assert_called_with(
                card=card,
                state=f.state
            )
            mock_StateLog.objects.filter.return_value.order_by.assert_called_with(
                '-entered',
            )
            assert 20 == duration
