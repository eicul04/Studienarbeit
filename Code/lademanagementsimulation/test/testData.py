import unittest

from data import get_available_solar_power


class TestData(unittest.TestCase):

    # TODO mock objects
    def test_get_available_solar_power(self):
        self.assertEqual(get_available_solar_power(100, 680), 32)


if __name__ == '__main__':
    unittest.main()
