import copy
from enum import Enum
from simulationData import create_plotly_table
from simulationManagementCalculation import calculate_charging_time
from simulationManagementChecks import check_if_parking_time_over

import numpy as np
import dataChecks
import data


class Algorithm(Enum):
    POLLING_FIFO = "pollingFIFO"
    POLLING_EVEN_DISTRIBUTION = "pollingEvenDistribution"


def start_simulation(solar_peak_power, max_charging_time, charging_power_pro_bev,
                     bev_parking_management, bev_data, table_dict, simulation_data, algorithm):
    algorithm_module = __import__(algorithm.value)
    simulate_day(solar_peak_power, max_charging_time, charging_power_pro_bev, bev_parking_management,
                 bev_data, table_dict, simulation_data, algorithm_module)


def simulate_day(solar_peak_power, max_charging_time, charging_power_pro_bev, bev_parking_management,
                 bev_data, table_dict, simulation_data, algorithm_module):
    day_in_minute_steps = list(np.around(np.arange(480, 960 + 1, 1), 1))
    for minute in day_in_minute_steps:
        check_and_update_parking_data(solar_peak_power, minute, max_charging_time,
                                      charging_power_pro_bev, bev_parking_management, algorithm_module, bev_data,
                                      simulation_data)
        safe_bev_dict_per_minute(minute, bev_parking_management, bev_data, table_dict, solar_peak_power)
        safe_waiting_list_per_minute(bev_parking_management, simulation_data, minute)
        safe_charging_list_per_minute(bev_parking_management, simulation_data, minute)


def check_and_update_parking_data(solar_peak_power, minute, max_charging_time,
                                  charging_power_pro_bev, bev_parking_management, algorithm_module, bev_data,
                                  simulation_data):
    bev_parking_management.update_waiting_bevs(minute)
    update_charging_time(minute, bev_parking_management)
    check_if_charging_time_over(minute, max_charging_time, bev_parking_management, algorithm_module)
    check_if_parking_time_over(minute, bev_parking_management)
    if dataChecks.check_availability_solar_power(solar_peak_power, minute):
        available_solar_power = data.get_available_solar_power(solar_peak_power, minute)
        update_charging_data(minute, available_solar_power, charging_power_pro_bev, bev_parking_management,
                             algorithm_module, bev_data, simulation_data)
        update_fueled_solar_energy(available_solar_power, bev_parking_management)


def add_charging_bevs(number_of_new_bevs_charging, minute, bev_parking_management):
    number_of_new_bevs_charging_as_list = list(range(0, number_of_new_bevs_charging))
    for item in number_of_new_bevs_charging_as_list:
        bev_parking_management.start_charging(bev_parking_management.waiting_bevs_list.get_first_waiting_bev_of_list(),
                                              minute)


def remove_charging_bevs(overflow_of_bevs_charging, bev_parking_management, algorithm_module, bev_data):
    overflow_of_bevs_charging_as_list = list(range(0, overflow_of_bevs_charging))
    for item in overflow_of_bevs_charging_as_list:
        id_bev = bev_parking_management.charging_bevs_list.get_first_charging_bev_of_list()
        algorithm_module.after_charging(id_bev, bev_parking_management)
        bev_data.increase_number_of_interrupted_charging_processes()
        bev_parking_management.stop_charging(id_bev)


def check_if_charging_time_over(current_minute, max_charging_time, bev_parking_management, algorithm_module):
    for id_bev in bev_parking_management.charging_bevs_list.get_charging_bevs_list():
        charging_start = bev_parking_management.bevs_dict.get_charging_start(id_bev)
        charging_time = calculate_charging_time(current_minute, charging_start)
        if charging_time >= max_charging_time:
            algorithm_module.after_charging(id_bev, bev_parking_management)
            bev_parking_management.stop_charging(id_bev)
    bev_parking_management.remove_from_list(bev_parking_management.charging_bevs_list)


def update_fueled_solar_energy(available_solar_power, bev_parking_management):
    number_of_charging_bevs = bev_parking_management.charging_bevs_list.get_number_of_charging_bevs()
    if number_of_charging_bevs != 0:
        charging_power_per_bev = get_charging_power_per_bev(available_solar_power, number_of_charging_bevs)
        for id_bev in bev_parking_management.charging_bevs_list.get_charging_bevs_list():
            bev_parking_management.bevs_dict.set_fueled_solar_energy(id_bev, charging_power_per_bev)


def update_charging_data(minute, available_solar_power, charging_power_pro_bev, bev_parking_management,
                         algorithm_module, bev_data, simulation_data):
    number_of_virtual_charging_stations = calculate_number_of_virtual_charging_stations(
        available_solar_power,
        charging_power_pro_bev)
    number_of_charging_bevs = bev_parking_management.charging_bevs_list.get_number_of_charging_bevs()
    update_charging_bevs(number_of_virtual_charging_stations, number_of_charging_bevs, minute, available_solar_power,
                         bev_parking_management, algorithm_module, bev_data, simulation_data)


def update_charging_bevs(number_of_virtual_charging_stations, number_of_charging_bevs, minute,
                         available_solar_power, bev_parking_management, algorithm_module, bev_data, simulation_data):
    if number_of_charging_bevs < number_of_virtual_charging_stations:
        add_charging_bevs(calculate_number_of_new_bevs_charging(number_of_virtual_charging_stations,
                                                                number_of_charging_bevs, minute, available_solar_power,
                                                                bev_parking_management, simulation_data),
                          minute, bev_parking_management)
    elif number_of_charging_bevs > number_of_virtual_charging_stations:
        remove_charging_bevs(calculate_overflow_of_bevs_charging(number_of_virtual_charging_stations,
                                                                 number_of_charging_bevs), bev_parking_management,
                             algorithm_module, bev_data)


def update_charging_time(minute, bev_parking_management):
    for id_bev in bev_parking_management.charging_bevs_list.get_charging_bevs_list():
        charging_time = calculate_charging_time(minute, bev_parking_management.bevs_dict.get_charging_start(id_bev))
        bev_parking_management.bevs_dict.set_charging_time(id_bev, charging_time)


def calculate_number_of_virtual_charging_stations(available_solar_power, charging_power_pro_bev):
    if available_solar_power <= charging_power_pro_bev:
        return 1
    if available_solar_power % charging_power_pro_bev == 0:
        return int(available_solar_power / charging_power_pro_bev)
    remaining_charging_capacity = available_solar_power % charging_power_pro_bev
    # + 1 für BEV, das dann die Reste tankt
    return int((available_solar_power - remaining_charging_capacity) / charging_power_pro_bev) + 1


def get_charging_power_per_bev(available_solar_power, number_of_charging_bevs):
    return available_solar_power / number_of_charging_bevs


def calculate_number_of_free_virtual_charging_stations(number_of_virtual_charging_stations, number_of_charging_bevs):
    return number_of_virtual_charging_stations - number_of_charging_bevs


def calculate_number_of_new_bevs_charging(number_of_virtual_charging_stations, number_of_charging_bevs, minute,
                                          available_solar_power, bev_parking_management, simulation_data):
    number_of_free_virtual_charging_stations = calculate_number_of_free_virtual_charging_stations(
        number_of_virtual_charging_stations, number_of_charging_bevs)
    if bev_parking_management.waiting_bevs_list.get_number_of_waiting_bevs() == 0:
        safe_unused_solar_energy(available_solar_power, simulation_data)
        print("Solarleistung wird in Leitung eingespeist")
        return 0
    elif bev_parking_management.waiting_bevs_list.get_number_of_waiting_bevs() < number_of_free_virtual_charging_stations:
        return bev_parking_management.waiting_bevs_list.get_number_of_waiting_bevs()
    return number_of_free_virtual_charging_stations


def calculate_overflow_of_bevs_charging(number_of_virtual_charging_stations, number_of_charging_bevs):
    return number_of_charging_bevs - number_of_virtual_charging_stations


def safe_bev_dict_per_minute(minute, bev_parking_management, bev_data, table_dict, solar_peak_power):
    current_bevs_dict = copy.deepcopy(bev_parking_management.bevs_dict)
    bev_data.add_bev_data_per_minute_dict(minute, current_bevs_dict)
    bev_dict_specific_minute = bev_data.get_bev_data_per_minute_dict(minute)
    current_table = create_plotly_table(bev_dict_specific_minute, solar_peak_power,
                                        minute)
    table_dict.add_table(minute, current_table)


def safe_waiting_list_per_minute(bev_parking_management, simulation_data, minute):
    waiting_list = copy.deepcopy(bev_parking_management.waiting_bevs_list.get_waiting_bevs_list())
    simulation_data.add_waiting_list_to_dict(minute, waiting_list)


def safe_charging_list_per_minute(bev_parking_management, simulation_data, minute):
    charging_list = copy.deepcopy(bev_parking_management.charging_bevs_list.get_charging_bevs_list())
    simulation_data.add_charging_list_to_dict(minute, charging_list)


def safe_unused_solar_energy(available_solar_power, simulation_data):
    simulation_data.add_unused_solar_energy(copy.deepcopy(available_solar_power))
