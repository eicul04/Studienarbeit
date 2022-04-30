from collections import OrderedDict

import numpy as np

from calculation import calculate_available_solar_power_per_bev
from chargingStationOccupancy import add_charging_bevs_if_free_charging_stations, update_unused_solar_energy
from data import get_available_solar_power
from forecastCalculation import get_available_solar_power_in_parking_interval_dict, calculate_fair_share_charging_energy
from simulateDay import simulate_day
from simulateDayForecast import simulate_day_forecast
from simulationData import safe_bev_dict_per_minute, safe_charging_list_per_minute, safe_bev_dict_per_minute_forecast, \
    safe_available_solar_power_per_bev_per_minute
from simulationService import update_charging_time, calculate_charging_time, update_fueled_solar_energy, \
    get_charging_power_per_bev, calculate_unused_solar_energy, safe_unused_solar_energy, \
    calculate_new_charging_energy, calculate_parking_end
from timeTransformation import in_minutes


def start_simulation(solar_peak_power, charging_power_pro_bev,
                     simulation_day, bev_data, table_dict, simulation_data, minute_interval):
    day_in_minute_interval_steps = list(np.around(np.arange(480, 960 + 1, minute_interval), 1))
    for minute in day_in_minute_interval_steps:
        init_simulation_data(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data,
                             minute_interval)
    set_fair_charging_energy(simulation_day, simulation_data, minute_interval)
    simulation_day.reset_simulation_day()
    for minute in day_in_minute_interval_steps:
        print("\n")
        print("Minute: ", minute)
        simulate_day_forecast(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data)
        print("Waiting BEVs: ", simulation_day.waiting_bevs_list.get_waiting_bevs_list())
        safe_bev_dict_per_minute_forecast(minute, simulation_day, bev_data, table_dict, solar_peak_power)
        # Solar-Energie die im letzten, vergangenen Minuten-Intervall getankt wurde
        available_solar_power_last_interval = get_available_solar_power(solar_peak_power, minute - minute_interval)
        update_fueled_solar_energy(available_solar_power_last_interval, simulation_day, minute_interval, minute,
                                   simulation_data)
        update_charging_bevs(solar_peak_power, minute,
                             charging_power_pro_bev, simulation_day, bev_data,
                             simulation_data, minute_interval)
        print("Charging BEVs: ", simulation_day.charging_bevs_list.get_charging_bevs_list())
        for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
            number_of_charging_bevs = simulation_day.charging_bevs_list.get_number_of_charging_bevs()
            available_solar_power = get_available_solar_power(solar_peak_power, minute)
            charging_power_real_per_bev = get_charging_power_per_bev(available_solar_power, number_of_charging_bevs)
            print("minute before saving", minute)
            bev_data.add_charging_power_per_bev_per_minute_dict(id_bev, minute, charging_power_real_per_bev)
        safe_charging_list_per_minute(simulation_day, simulation_data, minute)
    # das auch noch das Intervall bis 960 abgedeckt ist
    update_fueled_solar_energy_for_last_interval(solar_peak_power, simulation_day, minute_interval, simulation_data)


def update_fueled_solar_energy_for_last_interval(solar_peak_power, simulation_day, minute_interval, simulation_data):
    minute = 960 + minute_interval
    available_solar_power_last_interval = get_available_solar_power(solar_peak_power, 960)
    update_fueled_solar_energy(available_solar_power_last_interval, simulation_day, minute_interval, minute,
                               simulation_data)


def init_simulation_data(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data,
                         minute_interval):
    simulate_day_forecast(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data)


def set_fair_charging_energy(simulation_day, simulation_data, minute_interval):
    for id_bev in simulation_day.bevs_dict.get_bevs_dict().keys():
        fair_share_charging_energy = get_fair_share_charging_energy(simulation_day, id_bev, simulation_data,
                                                                    minute_interval)
        simulation_day.bevs_dict.add_fair_share_charging_energy(id_bev, fair_share_charging_energy)


def update_charging_bevs(solar_peak_power, minute,
                         charging_power_pro_bev, simulation_day, bev_data,
                         simulation_data, minute_interval):
    update_charging_time(minute, simulation_day)
    # update_because_fair_charged_energy_reached(simulation_day)
    available_solar_power = get_available_solar_power(solar_peak_power, minute)
    update_charging_bevs_for_next_interval(available_solar_power, minute, charging_power_pro_bev, simulation_day,
                                           bev_data, simulation_data, minute_interval, solar_peak_power)
    number_of_charging_bevs = simulation_day.charging_bevs_list.get_number_of_charging_bevs()
    update_residual_charging_time(simulation_day, solar_peak_power, minute, minute_interval, simulation_data, number_of_charging_bevs)
    stop_parking_if_less_than_next_interval(simulation_day, minute, minute_interval, solar_peak_power,
                                            number_of_charging_bevs, simulation_data)


# TODO delete this method
def update_because_fair_charged_energy_reached(simulation_day):
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        fair_share_charging_energy = simulation_day.bevs_dict.get_fair_share_charging_energy(id_bev)
        already_fueled_charging_energy = simulation_day.bevs_dict.get_fueled_charging_energy(id_bev)
        if already_fueled_charging_energy is not None:
            if already_fueled_charging_energy >= fair_share_charging_energy:
                simulation_day.stop_charging(id_bev)
    simulation_day.remove_from_list(simulation_day.charging_bevs_list)


def update_charging_bevs_for_next_interval(available_solar_power, minute, charging_power_pro_bev, simulation_day,
                                           bev_data, simulation_data, minute_interval, solar_peak_power):
    add_charging_bevs_if_free_charging_stations(available_solar_power, minute, charging_power_pro_bev,
                                                simulation_day, bev_data, simulation_data, minute_interval,
                                                solar_peak_power)


def stop_parking_if_less_than_next_interval(simulation_day, current_minute, minute_interval, solar_peak_power,
                                            number_of_charging_bevs, simulation_data):
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        parking_end = in_minutes(calculate_parking_end(simulation_day.bevs_dict.get_parking_start(id_bev),
                                                       simulation_day.bevs_dict.get_parking_time(id_bev)))
        if (current_minute + minute_interval) > parking_end > current_minute:
            solar_power_per_bev_for_next_interval = calculate_available_solar_power_per_bev(solar_peak_power,
                                                                                            number_of_charging_bevs,
                                                                                            current_minute)
            update_because_parking_time_over(id_bev, parking_end, simulation_day, current_minute,
                                             solar_power_per_bev_for_next_interval, solar_peak_power, simulation_data)


def update_because_parking_time_over(id_bev, parking_end, simulation_day, minute, solar_power_per_bev_for_next_interval,
                                     solar_peak_power, simulation_data):
    residual_parking_time = parking_end - minute
    print("For ID BEV: ", id_bev)
    print("parking end", parking_end)
    print("minute", minute)
    set_bev_data_after_parking_time_over(id_bev, simulation_day, solar_power_per_bev_for_next_interval,
                                         residual_parking_time)
    stop_parking(id_bev, simulation_day)
    start_charging_of_new_bev(simulation_day, minute, residual_parking_time, solar_peak_power, simulation_data,
                              solar_power_per_bev_for_next_interval)


# TODO hier statt stufen funktion Mitte vom Interval nehmen
def update_residual_charging_time(simulation_day, solar_peak_power, minute, minute_interval, simulation_data, number_of_charging_bevs):
    print("Charging BEV Liste vor residual berechnung: ", simulation_day.charging_bevs_list.get_charging_bevs_list())
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        already_fueled_charging_energy = simulation_day.bevs_dict.get_fueled_charging_energy(id_bev)
        fair_share_charging_energy = simulation_day.bevs_dict.get_fair_share_charging_energy(id_bev)
        residual_charging_energy = get_residual_charging_energy(already_fueled_charging_energy,
                                                                fair_share_charging_energy)
        # TODO minute + minute_interval/2 (-> mod oder runden?)
        solar_power_per_bev_for_next_interval = calculate_available_solar_power_per_bev(solar_peak_power,
                                                                                        number_of_charging_bevs, minute)
        set_charging_end_if_less_than_next_interval(residual_charging_energy, solar_power_per_bev_for_next_interval,
                                                    simulation_day, id_bev, minute_interval, solar_peak_power, minute,
                                                    simulation_data)


def set_charging_end_if_less_than_next_interval(residual_charging_energy, solar_power_per_bev_for_next_interval,
                                                simulation_day,
                                                id_bev, minute_interval, solar_peak_power, minute, simulation_data):
    solar_energy_per_bev_for_next_interval = solar_power_per_bev_for_next_interval * (minute_interval / 60)
    if residual_charging_energy < solar_energy_per_bev_for_next_interval:
        print("Die Restladezeit des BEVS {} endet vor dem nächsten Interval".format(id_bev))
        if solar_power_per_bev_for_next_interval != 0:
            residual_charging_time = get_residual_charging_time(residual_charging_energy,
                                                                solar_power_per_bev_for_next_interval)
            update_because_residual_charging_time_over(residual_charging_time, id_bev, simulation_day, minute,
                                                       solar_power_per_bev_for_next_interval, minute_interval,
                                                       solar_peak_power, simulation_data)


def get_residual_charging_time(residual_charging_energy, solar_power_per_bev_for_next_interval):
    return (residual_charging_energy / solar_power_per_bev_for_next_interval) * 60


def get_residual_charging_energy(already_fueled_charging_energy, fair_share_charging_energy):
    return fair_share_charging_energy - already_fueled_charging_energy


def update_because_residual_charging_time_over(residual_charging_time, id_bev, simulation_day, minute,
                                               solar_power_per_bev_for_next_interval,
                                               minute_interval, solar_peak_power, simulation_data):
    set_bev_data_after_charging_time_over(residual_charging_time, id_bev, simulation_day, minute,
                                          solar_power_per_bev_for_next_interval, minute_interval)
    stop_charging(id_bev, simulation_day)
    start_charging_of_new_bev(simulation_day, minute, residual_charging_time, solar_peak_power, simulation_data,
                              solar_power_per_bev_for_next_interval)


def set_bev_data_after_charging_time_over(residual_charging_time, id_bev, simulation_day, minute,
                                          solar_power_per_bev_for_next_interval, minute_interval):
    charging_end = minute + residual_charging_time
    charging_start = simulation_day.bevs_dict.get_charging_start(id_bev)
    final_charging_time = charging_end - charging_start
    simulation_day.bevs_dict.set_charging_time(id_bev, final_charging_time)
    residual_solar_energy_till_charging_end = solar_power_per_bev_for_next_interval * (residual_charging_time / 60)
    print("Residual charging_time: ", residual_charging_time)
    print("residual_solar_energy_till_charging_end: ", residual_solar_energy_till_charging_end)
    simulation_day.bevs_dict.add_fueled_charging_energy(id_bev, residual_solar_energy_till_charging_end)


def set_bev_data_after_parking_time_over(id_bev, simulation_day, solar_power_per_bev_for_next_interval,
                                         residual_parking_time):
    residual_solar_energy_till_parking_end = solar_power_per_bev_for_next_interval * (residual_parking_time / 60)
    print("Residual parking time: ", residual_parking_time)
    print('residual_solar_energy_till_parking_end', residual_solar_energy_till_parking_end)
    simulation_day.bevs_dict.add_fueled_charging_energy(id_bev, residual_solar_energy_till_parking_end)
    update_charging_time(residual_parking_time, simulation_day)


def stop_charging(id_bev, simulation_day):
    simulation_day.stop_charging(id_bev)
    simulation_day.remove_from_list(simulation_day.charging_bevs_list)


def stop_parking(id_bev, simulation_day):
    simulation_day.stop_parking(id_bev)
    simulation_day.remove_from_list(simulation_day.charging_bevs_list)


def start_charging_of_new_bev(simulation_day, minute, residual_time, solar_peak_power, simulation_data,
                              solar_power_per_bev_for_next_interval):
    first_bev_waiting_on_list = simulation_day.waiting_bevs_list.get_first_waiting_bev_of_list()
    number_of_charging_bevs = simulation_day.charging_bevs_list.get_number_of_charging_bevs()
    if first_bev_waiting_on_list is not None:
        simulation_day.start_charging(first_bev_waiting_on_list)
        # TODO hier stückweise vs Stufen dings anpassen
        charging_start = minute + residual_time
        simulation_day.init_charging_data(first_bev_waiting_on_list, charging_start)
    elif first_bev_waiting_on_list is None and number_of_charging_bevs != 0:
        for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
            remaining_charging_power_per_bev = solar_power_per_bev_for_next_interval / number_of_charging_bevs
            charging_interval = residual_time
            new_charging_energy = calculate_new_charging_energy(remaining_charging_power_per_bev, charging_interval)
            simulation_day.bevs_dict.add_fueled_charging_energy(id_bev, new_charging_energy)
    else:
        unused_solar_energy_interval = residual_time
        unused_solar_power = get_available_solar_power(solar_peak_power, minute)
        safe_unused_solar_energy(calculate_unused_solar_energy(unused_solar_power, unused_solar_energy_interval),
                                 simulation_data)


def get_fair_share_charging_energy(simulation_day, id_bev, simulation_data, minute_interval):
    available_solar_power_per_bev_in_parking_interval_dict = OrderedDict(sorted(
        get_available_solar_power_in_parking_interval_dict(
            simulation_day, id_bev, simulation_data, minute_interval).items()))
    return calculate_fair_share_charging_energy(available_solar_power_per_bev_in_parking_interval_dict,
                                                minute_interval)
