from enum import Enum

from simulateDay import simulate_day
from simulationData import safe_charging_list_per_minute
from simulationService import calculate_charging_time, \
    calculate_number_of_new_bevs_charging, calculate_overflow_of_bevs_charging, \
    calculate_number_of_virtual_charging_stations, get_charging_power_per_bev

import numpy as np
import dataChecks
import data


class Algorithm(Enum):
    POLLING_FIFO = "pollingFIFO"
    POLLING_EVEN_DISTRIBUTION = "pollingEvenDistribution"


def start_simulation(solar_peak_power, max_charging_time, charging_power_pro_bev,
                     simulation_day, bev_data, table_dict, simulation_data, algorithm):
    algorithm_module = __import__(algorithm.value)
    day_in_minute_steps = list(np.around(np.arange(480, 960 + 1, 1), 1))
    for minute in day_in_minute_steps:
        simulate_day(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data)
        update_charging_bevs(solar_peak_power, minute, max_charging_time,
                             charging_power_pro_bev, simulation_day, algorithm_module, bev_data,
                             simulation_data)
        safe_charging_list_per_minute(simulation_day, simulation_data, minute)


def update_charging_bevs(solar_peak_power, minute, max_charging_time,
                         charging_power_pro_bev, simulation_day, algorithm_module, bev_data,
                         simulation_data):
    update_charging_time(minute, simulation_day)
    update_because_charging_time_over(minute, max_charging_time, simulation_day, algorithm_module)
    update_because_change_in_number_of_charging_stations(solar_peak_power, minute,
                                                         charging_power_pro_bev, simulation_day,
                                                         bev_data,
                                                         simulation_data)


def update_because_change_in_number_of_charging_stations(solar_peak_power, minute,
                                                         charging_power_pro_bev, simulation_day,
                                                         bev_data,
                                                         simulation_data):
    if dataChecks.check_availability_solar_power(solar_peak_power, minute):
        available_solar_power = data.get_available_solar_power(solar_peak_power, minute)
        update_charging_place_occupancy(available_solar_power, minute, charging_power_pro_bev, simulation_day,
                                        bev_data, simulation_data)
        update_fueled_solar_energy(available_solar_power, simulation_day)


def update_charging_place_occupancy(available_solar_power, minute, charging_power_pro_bev, simulation_day,
                                    bev_data, simulation_data):
    number_of_virtual_charging_stations = get_number_of_virtual_charging_stations(available_solar_power,
                                                                                  charging_power_pro_bev)
    number_of_charging_bevs = get_number_of_charging_bevs(simulation_day)
    number_of_available_charging_stations = get_number_of_available_charging_stations(
        number_of_virtual_charging_stations, number_of_charging_bevs)
    if number_of_available_charging_stations > 0:
        add_charging_bevs_because_of_free_places(calculate_number_of_new_bevs_charging(number_of_virtual_charging_stations,
                                                                                       number_of_charging_bevs, minute,
                                                                                       available_solar_power,
                                                                                       simulation_day, simulation_data),
                                                 minute, simulation_day)
    elif number_of_available_charging_stations < 0:
        remove_charging_bevs_because_of_lack_of_places(calculate_overflow_of_bevs_charging(number_of_virtual_charging_stations,
                                                                                           number_of_charging_bevs), simulation_day
                                                       , bev_data)


def get_number_of_virtual_charging_stations(available_solar_power, charging_power_pro_bev):
    return calculate_number_of_virtual_charging_stations(available_solar_power, charging_power_pro_bev)


def get_number_of_charging_bevs(simulation_day):
    return simulation_day.charging_bevs_list.get_number_of_charging_bevs()


def get_number_of_available_charging_stations(number_of_virtual_charging_stations, number_of_charging_bevs):
    return number_of_virtual_charging_stations - number_of_charging_bevs


def add_charging_bevs_because_of_free_places(number_of_new_bevs_charging, minute, simulation_day):
    number_of_new_bevs_charging_as_list = list(range(0, number_of_new_bevs_charging))
    for item in number_of_new_bevs_charging_as_list:
        simulation_day.start_charging(simulation_day.waiting_bevs_list.get_first_waiting_bev_of_list(),
                                      minute)


def remove_charging_bevs_because_of_lack_of_places(overflow_of_bevs_charging, simulation_day, bev_data):
    overflow_of_bevs_charging_as_list = list(range(0, overflow_of_bevs_charging))
    for item in overflow_of_bevs_charging_as_list:
        id_bev = simulation_day.charging_bevs_list.get_first_charging_bev_of_list()
        simulation_day.waiting_bevs_list.add_bev(id_bev)
        bev_data.increase_number_of_interrupted_charging_processes()
        print("interrupted charging process")
        simulation_day.stop_charging(id_bev)
    simulation_day.remove_from_list(simulation_day.charging_bevs_list)


def update_because_charging_time_over(current_minute, max_charging_time, simulation_day, algorithm_module):
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        charging_start = simulation_day.bevs_dict.get_charging_start(id_bev)
        charging_time = calculate_charging_time(current_minute, charging_start)
        if charging_time >= max_charging_time:
            algorithm_module.after_charging(id_bev, simulation_day)
            simulation_day.stop_charging(id_bev)
    simulation_day.remove_from_list(simulation_day.charging_bevs_list)


def update_fueled_solar_energy(available_solar_power, simulation_day):
    number_of_charging_bevs = simulation_day.charging_bevs_list.get_number_of_charging_bevs()
    if number_of_charging_bevs != 0:
        charging_power_per_bev = get_charging_power_per_bev(available_solar_power, number_of_charging_bevs)
        for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
            simulation_day.bevs_dict.set_fueled_solar_energy(id_bev, charging_power_per_bev)


def update_charging_time(minute, simulation_day):
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        charging_time = calculate_charging_time(minute, simulation_day.bevs_dict.get_charging_start(id_bev))
        simulation_day.bevs_dict.set_charging_time(id_bev, charging_time)



