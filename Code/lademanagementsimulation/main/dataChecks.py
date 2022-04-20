import calculation


def check_availability_solar_power(solar_peak_power, minute):
    return is_available_solar_power_enough(calculation.get_available_solar_power_interpolated(solar_peak_power, minute))


# TODO Wert definieren statt 0 oder als Input value
def is_available_solar_power_enough(available_solar_power):
    if available_solar_power <= 0:
        return False
    return True
