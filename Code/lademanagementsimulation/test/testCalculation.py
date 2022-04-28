import unittest

from calculation import get_available_solar_power_quadratic_interpolated


class TestCalculation(unittest.TestCase):

    def test_get_available_solar_power_interpolated_1(self):
        self.assertEqual(get_available_solar_power_quadratic_interpolated(100, 521), 5.2)

    def test_get_available_solar_power_interpolated_2(self):
        self.assertEqual(get_available_solar_power_quadratic_interpolated(100, 531), 8.58)


if __name__ == '__main__':
    unittest.main()
