import unittest2


class EfficiencyTests(unittest2.TestCase):
    """
    Tests for the kardboard.services.teams.EfficiencyStats service
    """
    def _get_target_class(self):
        from kardboard.services.teams import EfficiencyStats
        return EfficiencyStats

    def test_given_a_mapping_and_data_returns_a_sum(self):
        """
        If the calculate method is called with a mapping of state names to
        categories and a dictionary of data with state names and counts,
        it returns a sum.
        """

        data = {
            'Backlog': 20,
            'Elaboration': 2,
            'Ready: Building': 1,
            'Building': 5,
            'Ready: Test': 3,
            'Test': 2,
            'Ready: Deploy': 1,
            'Done': 177,
        }

        mapping = {
            'Queued': ('Backlog', ),
            'In Process': ('Elaboration', 'Building', 'Test'),
            'Waiting': ('Ready: Building', 'Ready: Test', 'Ready: Deploy'),
            'Finished': ('Done', )
        }

        expected = {
            'Queued': 20,
            'In Process': 9,
            'Waiting': 5,
            'Finished': 177,
        }

        es = self._get_target_class()()
        result = es.calculate(data, mapping)

        assert expected == result

    def test_can_provide_instance_mapping(self):
        """
        You should be able to provide an EfficiencyStats a single
        instance mapping and have it use it caclulate.
        """

        mapping = {
            'Queued': ('Backlog', ),
            'In Process': ('Elaboration', 'Building', 'Test'),
            'Waiting': ('Ready: Building', 'Ready: Test', 'Ready: Deploy'),
            'Finished': ('Done', )
        }

        es = self._get_target_class()(mapping=mapping)

        data = {
            'Backlog': 20,
            'Elaboration': 2,
            'Ready: Building': 1,
            'Building': 5,
            'Ready: Test': 3,
            'Test': 2,
            'Ready: Deploy': 1,
            'Done': 177,
        }

        expected = {
            'Queued': 20,
            'In Process': 9,
            'Waiting': 5,
            'Finished': 177,
        }

        result = es.calculate(data)
        assert expected == result

    def test_can_reuse_instance_mapping(self):
        """
        You should be able to provide an EfficiencyStats a single
        instance mapping and have it use it for multiple calls.
        """

        mapping = {
            'Queued': ('Backlog', ),
            'In Process': ('Elaboration', 'Building', 'Test'),
            'Waiting': ('Ready: Building', 'Ready: Test', 'Ready: Deploy'),
            'Finished': ('Done', )
        }

        es = self._get_target_class()(mapping=mapping)

        data = {
            'Backlog': 20,
            'Elaboration': 2,
            'Ready: Building': 1,
            'Building': 5,
            'Ready: Test': 3,
            'Test': 2,
            'Ready: Deploy': 1,
            'Done': 177,
        }

        result = es.calculate(data)

        data2 = {
            'Backlog': 1,
            'Elaboration': 5,
            'Ready: Building': 10,
            'Building': 20,
            'Ready: Test': 5,
            'Test': 7,
            'Ready: Deploy': 3,
            'Done': 200,
        }
        result2 = es.calculate(data2)

        assert result != result2

    def test_states_in_mapping_not_in_data(self):
        """
        States in the mapping that don't also appear in the data
        should be safely ignored.
        """

        mapping = {
            'Queued': ('Backlog', ),
            'In Process': ('Elaboration', 'UX', 'Building', 'Test'),
            'Waiting': ('Ready: Building', 'Ready: Test', 'Ready: Deploy'),
            'Finished': ('Done', )
        }

        es = self._get_target_class()(mapping=mapping)

        data = {
            'Backlog': 1,
            'Elaboration': 5,
            'Ready: Building': 10,
            'Building': 20,
            'Ready: Test': 5,
            'Test': 7,
            'Ready: Deploy': 3,
            'Done': 200,
        }
        expected = {
            'Queued': 1,
            'In Process': 32,
            'Waiting': 18,
            'Finished': 200,
        }

        result = es.calculate(data)
        assert expected == result

    def test_states_in_data_not_in_mapping(self):
        """
        States in the data that don't also appear in the mapping
        should be safely ignored.
        """

        mapping = {
            'Queued': ('Backlog', ),
            'In Process': ('Building',),
            'Waiting': ('Ready: Building', ),
        }

        es = self._get_target_class()(mapping=mapping)

        data = {
            'Backlog': 1,
            'Elaboration': 5,
            'Ready: Building': 10,
            'Building': 20,
            'Ready: Test': 5,
            'Test': 7,
            'Ready: Deploy': 3,
            'Done': 200,
        }
        expected = {
            'Queued': 1,
            'In Process': 20,
            'Waiting': 10,
        }

        result = es.calculate(data)
        assert expected == result

    def test_make_incremental(self):
        """
        If given a series of dictionaries and a key,
        loop through the series and make each key in each slice
        appear to be incrementing from 0.
        """

        data = [
            {'Todo': 5, 'Doing': 3, 'Done': 10},
            {'Todo': 4, 'Doing': 3, 'Done': 11},
            {'Todo': 3, 'Doing': 5, 'Done': 13},
            {'Todo': 2, 'Doing': 5, 'Done': 13},
        ]
        expected = [
            {'Todo': 5, 'Doing': 3, 'Done': 0},
            {'Todo': 4, 'Doing': 3, 'Done': 1},
            {'Todo': 3, 'Doing': 5, 'Done': 2},
            {'Todo': 2, 'Doing': 5, 'Done': 0},
        ]

        es = self._get_target_class()()
        result = es.make_incremental(data, 'Done')
        assert expected == result
