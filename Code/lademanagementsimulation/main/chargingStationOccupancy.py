from data import get_available_solar_power
from dataChecks import check_availability_solar_power
from simulationService import update_fueled_solar_energy, calculate_number_of_new_bevs_charging, \
    calculate_overflow_of_bevs_charging, calculate_number_of_charging_stations


def add_charging_bevs_if_free_charging_stations(available_solar_power, minute, charging_power_pro_bev, simulation_day,
                                                bev_data, simulation_data, minute_interval):
    number_of_charging_stations = get_number_of_charging_stations(available_solar_power,
                                                                  charging_power_pro_bev)
    number_of_charging_bevs = get_number_of_charging_bevs(simulation_day)
    number_of_available_charging_stations = get_number_of_available_charging_stations(
        number_of_charging_stations, number_of_charging_bevs)
    if number_of_available_charging_stations > 0:
        add_charging_bevs_because_of_free_charging_stations(calculate_number_of_new_bevs_charging(number_of_charging_stations,
                                                                                                  number_of_charging_bevs, minute,
                                                                                                  available_solar_power,
                                                                                                  simulation_day, simulation_data, minute_interval),
                                                            minute, simulation_day)


def get_number_of_charging_stations(available_solar_power, charging_power_pro_bev):
    return calculate_number_of_charging_stations(available_solar_power, charging_power_pro_bev)


def get_number_of_charging_bevs(simulation_day):
    return simulation_day.charging_bevs_list.get_number_of_charging_bevs()


def get_number_of_available_charging_stations(number_of_virtual_charging_stations, number_of_charging_bevs):
    return number_of_virtual_charging_stations - number_of_charging_bevs


def add_charging_bevs_because_of_free_charging_stations(number_of_new_bevs_charging, minute, simulation_day):
    number_of_new_bevs_charging_as_list = list(range(0, number_of_new_bevs_charging))
    for item in number_of_new_bevs_charging_as_list:
        simulation_day.start_charging(simulation_day.waiting_bevs_list.get_first_waiting_bev_of_list())
        simulation_day.init_charging_data(simulation_day.waiting_bevs_list.get_first_waiting_bev_of_list(), minute)

