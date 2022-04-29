from collections import OrderedDict

import numpy as np

from calculation import calculate_available_solar_power_per_bev
from chargingStationOccupancy import add_charging_bevs_if_free_charging_stations
from data import get_available_solar_power
from dataChecks import check_availability_solar_power
from forecastCalculation import get_available_solar_power_in_parking_interval_dict, calculate_fair_share_charging_energy
from simulateDay import simulate_day
from simulationData import safe_bev_dict_per_minute, safe_charging_list_per_minute
from simulationService import update_charging_time, calculate_charging_time, update_fueled_solar_energy


def start_simulation(solar_peak_power, charging_power_pro_bev,
                     simulation_day, bev_data, table_dict, simulation_data, minute_interval):
    day_in_minute_steps = list(np.around(np.arange(480, 960 + 1, 1), 1))
    for minute in day_in_minute_steps:
        init_simulation_data(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data)
    set_fair_charging_energy(simulation_day, simulation_data, minute_interval)
    for minute in day_in_minute_steps:
        simulate_day(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data)
        safe_bev_dict_per_minute(minute, simulation_day, bev_data, table_dict, solar_peak_power)
        update_charging_bevs(solar_peak_power, minute,
                             charging_power_pro_bev, simulation_day, bev_data,
                             simulation_data, minute_interval)
        safe_charging_list_per_minute(simulation_day, simulation_data, minute)


def init_simulation_data(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data):
    simulate_day(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data)


def set_fair_charging_energy(simulation_day, simulation_data, minute_interval):
    for id_bev in simulation_day.bevs_dict.get_bevs_dict().keys():
        fair_share_charging_energy = get_fair_share_charging_energy(simulation_day, id_bev, simulation_data, minute_interval)
        simulation_day.bevs_dict.add_fair_share_charging_energy(id_bev, fair_share_charging_energy)


def update_charging_bevs(solar_peak_power, minute,
                         charging_power_pro_bev, simulation_day, bev_data,
                         simulation_data, minute_interval):
    update_charging_time(minute, simulation_day)
    update_because_fair_charged_energy_reached(simulation_day)
    available_solar_power = get_available_solar_power(solar_peak_power, minute)
    update_charging_bevs_for_next_interval(available_solar_power, minute, charging_power_pro_bev, simulation_day,
                                                bev_data, simulation_data, minute_interval)
    update_fueled_solar_energy(available_solar_power, simulation_day, minute_interval)
    # update_residual_charging_time(simulation_day)


def update_because_fair_charged_energy_reached(simulation_day):
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        fair_share_charging_energy = simulation_day.bevs_dict.get_fair_share_charging_energy(id_bev)
        already_fueled_charging_energy = simulation_day.bevs_dict.get_fueled_charging_energy(id_bev)
        if already_fueled_charging_energy is not None:
            if already_fueled_charging_energy >= fair_share_charging_energy:
                simulation_day.stop_charging(id_bev)
    simulation_day.remove_from_list(simulation_day.charging_bevs_list)


def update_charging_bevs_for_next_interval(available_solar_power, minute, charging_power_pro_bev, simulation_day,
                                                bev_data, simulation_data, minute_interval):
    add_charging_bevs_if_free_charging_stations(available_solar_power, minute, charging_power_pro_bev,
                                                simulation_day, bev_data, simulation_data, minute_interval)


# TODO hier statt stufen funktion Mitte vom Interval nehmen
def update_residual_charging_time(simulation_day, solar_peak_power, minute, minute_interval):
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        already_fueled_charging_energy = simulation_day.bevs_dict.get_fueled_charging_energy(id_bev)
        fair_share_charging_energy = simulation_day.bevs_dict.get_fair_share_charging_energy(id_bev)
        residual_charging_energy = get_residual_charging_energy(already_fueled_charging_energy, fair_share_charging_energy)
        # TODO minute + minute_interval/2 (-> mod oder runden?)
        number_of_charging_bevs = len(simulation_day.charging_bevs_list.get_charging_bevs_list())
        solar_power_per_bev_for_next_interval = calculate_available_solar_power_per_bev(solar_peak_power,
                                                                                        number_of_charging_bevs, minute + minute_interval)
        set_charging_end_if_less_than_next_interval(residual_charging_energy, solar_power_per_bev_for_next_interval,
                                                    simulation_day, id_bev, minute_interval, solar_peak_power, minute)


# Wenn residual_c_t < als nächstes Intervall
# dann rechne auf charging time residual_c_t und update anhand diesem wert den fueled solar energy wert
# und stoppe das auto von charging
# TODO macht kein Sinn, dann wäre von der Viertelstunde richtig viel ungenutzt
# NUR Solarleistung soll über 15min Intervalle approximiert werden! Der Tag muss mit Minuten durchlaufen
def set_charging_end_if_less_than_next_interval(residual_charging_energy, solar_power_per_bev_for_next_interval, simulation_day,
                                                id_bev, minute_interval, solar_peak_power, minute):
    if solar_power_per_bev_for_next_interval != 0:
        residual_charging_time = get_residual_charging_time(residual_charging_energy, solar_power_per_bev_for_next_interval)
        simulation_day.bevs_dict.set_charging_time(id_bev, residual_charging_time)

        minutes_in_minute_interval_steps = list(range(0, minute_interval, 1))
        for minute_in_interval in minutes_in_minute_interval_steps:
            update_because_residual_charging_time_over(minute_in_interval)
            available_solar_power = get_available_solar_power(solar_peak_power, minute)
            update_fueled_solar_energy(available_solar_power, simulation_day, minute_interval)


def get_residual_charging_time(residual_charging_energy, solar_power_per_bev_for_next_interval):
    return (residual_charging_energy / solar_power_per_bev_for_next_interval) * 60


def get_residual_charging_energy(already_fueled_charging_energy, fair_share_charging_energy):
    return already_fueled_charging_energy - fair_share_charging_energy


def update_because_residual_charging_time_over(minute_in_interval):
    return ("bla")
    # if charging_time < charging_end
    # calculate_residual_time -> stop charging after residual time passed


def get_fair_share_charging_energy(simulation_day, id_bev, simulation_data, minute_interval):
    available_solar_power_per_bev_in_parking_interval_dict = OrderedDict(sorted(
        get_available_solar_power_in_parking_interval_dict(
            simulation_day, id_bev, simulation_data, minute_interval).items()))
    return calculate_fair_share_charging_energy(available_solar_power_per_bev_in_parking_interval_dict,
                                                                      minute_interval)

