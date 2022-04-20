import unittest
from unittest.mock import MagicMock, Mock

from main.distributionAlgorithmPolling import calculate_number_of_virtual_charging_stations, \
    calculate_number_of_new_bevs_charging, get_number_of_waiting_bevs


class TestDistributionAlgorithmPolling(unittest.TestCase):

    def setUp(self) -> None:
        waiting_bevs = [5]

    def test_calculate_number_of_possible_bevs_charging_less_two(self):
        self.assertEqual(calculate_number_of_virtual_charging_stations(1), 1)

    def test_calculate_number_of_possible_bevs_charging_more_two_equal(self):
        self.assertEqual(calculate_number_of_virtual_charging_stations(4), 2)

    def test_calculate_number_of_possible_bevs_charging_more_two_unequal(self):
        self.assertEqual(calculate_number_of_virtual_charging_stations(5), 2)

    def test_calculate_number_of_new_bevs_charging(self):
        # self.get_number_of_waiting_bevs() = 0
        #MagicMock(return_value=0)
        self.assertEqual(calculate_number_of_new_bevs_charging(5, 3), 1)


if __name__ == '__main__':
    unittest.main()
