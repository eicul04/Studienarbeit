from enum import Enum

from chargingStationOccupancy import add_charging_bevs_if_free_charging_stations
from simulateDay import simulate_day
from simulationData import safe_charging_list_per_minute, safe_bev_dict_per_minute
from simulationService import calculate_charging_time, calculate_overflow_of_bevs_charging, \
    calculate_number_of_charging_stations, get_charging_power_per_bev, update_fueled_solar_energy, \
    update_charging_time

import numpy as np
import dataChecks
import data


class Algorithm(Enum):
    POLLING_FIFO = "pollingFIFO"
    POLLING_EVEN_DISTRIBUTION = "pollingEvenDistribution"


def start_simulation(solar_peak_power, max_charging_time, charging_power_pro_bev,
                     simulation_day, bev_data, table_dict, simulation_data, algorithm, minute_interval):
    algorithm_module = __import__(algorithm.value)
    day_in_minute_steps = list(np.around(np.arange(480, 960 + 1, 1), 1))
    for minute in day_in_minute_steps:
        simulate_day(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data)
        safe_bev_dict_per_minute(minute, simulation_day, bev_data, table_dict, solar_peak_power)
        update_charging_bevs(solar_peak_power, minute, max_charging_time,
                             charging_power_pro_bev, simulation_day, algorithm_module, bev_data,
                             simulation_data, minute_interval)
        safe_charging_list_per_minute(simulation_day, simulation_data, minute)


def update_charging_bevs(solar_peak_power, minute, max_charging_time,
                         charging_power_pro_bev, simulation_day, algorithm_module, bev_data,
                         simulation_data, minute_interval):
    update_charging_time(minute, simulation_day)
    update_because_charging_time_over(minute, max_charging_time, simulation_day, algorithm_module)
    if dataChecks.check_availability_solar_power(solar_peak_power, minute):
        available_solar_power = data.get_available_solar_power(solar_peak_power, minute)
        add_charging_bevs_if_free_charging_stations(available_solar_power, minute, charging_power_pro_bev,
                                                    simulation_day,
                                                    bev_data, simulation_data, minute_interval)
        update_fueled_solar_energy(available_solar_power, simulation_day, minute_interval)


def update_because_charging_time_over(current_minute, max_charging_time, simulation_day, algorithm_module):
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        charging_start = simulation_day.bevs_dict.get_charging_start(id_bev)
        charging_time = calculate_charging_time(current_minute, charging_start)
        if charging_time >= max_charging_time:
            algorithm_module.after_charging(id_bev, simulation_day)
            simulation_day.stop_charging(id_bev)
    simulation_day.remove_from_list(simulation_day.charging_bevs_list)




