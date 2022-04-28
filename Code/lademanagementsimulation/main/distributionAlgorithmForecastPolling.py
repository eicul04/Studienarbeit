from collections import OrderedDict

import numpy as np

from chargingStationOccupancy import update_because_change_in_number_of_charging_stations
from forecastCalculation import get_available_solar_power_in_parking_interval_dict, calculate_fair_share_charging_energy
from simulateDay import simulate_day
from simulationData import safe_bev_dict_per_minute, safe_charging_list_per_minute
from simulationService import update_charging_time, calculate_charging_time


def start_simulation(solar_peak_power, charging_power_pro_bev,
                     simulation_day, bev_data, table_dict, simulation_data, minute_interval):
    day_in_minute_steps = list(np.around(np.arange(480, 960 + 1, minute_interval), 1))
    for minute in day_in_minute_steps:
        init_simulation_data(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data)
    for minute in day_in_minute_steps:
        simulate_day(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data)
        safe_bev_dict_per_minute(minute, simulation_day, bev_data, table_dict, solar_peak_power)
        update_charging_bevs(solar_peak_power, minute,
                             charging_power_pro_bev, simulation_day, bev_data,
                             simulation_data, minute_interval)
        safe_charging_list_per_minute(simulation_day, simulation_data, minute)


def init_simulation_data(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data):
    simulate_day(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data)


def update_charging_bevs(solar_peak_power, minute,
                         charging_power_pro_bev, simulation_day, bev_data,
                         simulation_data, minute_interval):
    update_charging_time(minute, simulation_day)
    update_because_fair_charged_energy_reached(simulation_day)
    # update_because_charging_time_over(minute, fair_charging_time, simulation_day)
    update_because_change_in_number_of_charging_stations(solar_peak_power, minute,
                                                         charging_power_pro_bev, simulation_day,
                                                         bev_data,
                                                         simulation_data, minute_interval)


# TODO fair_charged_energy im init Prozess in bev_dict schreiben -> bev_data[3]
def update_because_fair_charged_energy_reached(simulation_day):
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        # get fair charged energy
        # check if already_fueled_charging_energy < fair_charged_energy
        # calculate residual_charging_energy = already_fueled_charging_energy - fair_charged_energy
        # if residual_charging_energy < available_solar_energy_for_bev_in_next_interval
        # calculate_residual_time -> stop charging after residual time passed
        # else stop charging



def get_fair_share_charging_energy(simulation_day, id_bev, simulation_data, minute_interval):
    available_solar_power_per_bev_in_parking_interval_dict = OrderedDict(sorted(
        get_available_solar_power_in_parking_interval_dict(
            simulation_day, id_bev, simulation_data, minute_interval).items()))
    return calculate_fair_share_charging_energy(available_solar_power_per_bev_in_parking_interval_dict,
                                                                      minute_interval)



def update_because_charging_time_over(current_minute, fair_charging_time, simulation_day):
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        charging_start = simulation_day.bevs_dict.get_charging_start(id_bev)
        charging_time = calculate_charging_time(current_minute, charging_start)
        if charging_time >= fair_charging_time:
            simulation_day.stop_charging(id_bev)
    simulation_day.remove_from_list(simulation_day.charging_bevs_list)