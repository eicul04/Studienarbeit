import copy
from collections import OrderedDict

import numpy as np

from calculation import calculate_available_solar_power_per_bev, get_available_solar_power_linear_interpolated
from chargingStationOccupancy import add_charging_bev_from_optimization_plan, \
    get_number_of_charging_bevs, get_number_of_available_charging_stations, get_number_of_charging_stations, \
    update_unused_solar_energy, check_if_free_charging_stations, check_if_new_bevs_for_charging, \
    get_number_of_unoccupied_charging_stations, add_charging_bevs
from forecastCalculation import get_available_solar_power_in_parking_interval_dict, calculate_fair_share_charging_energy
from simulateDayForecast import update_waiting_bevs_forecast
from simulationClasses import ParkingState
from simulationData import safe_charging_list_per_minute, safe_bev_dict_per_minute_forecast
from simulationService import update_charging_time, update_fueled_solar_energy, \
    get_charging_power_per_bev, calculate_unused_solar_energy, safe_unused_solar_energy, \
    calculate_new_charging_energy, calculate_parking_end, check_if_solar_power_per_bev_for_next_interval_is_not_null, \
    get_residual_charging_time, get_residual_charging_energy, stop_charging, stop_parking, check_if_bev_on_waiting_list, \
    check_if_bev_on_charging_list, check_if_charging_energy_less_than_next_interval


def start_simulation(solar_peak_power, charging_power_pro_bev,
                     simulation_day, bev_data, table_dict, simulation_data, minute_interval):
    day_in_minute_interval_steps = list(np.around(np.arange(480, 960 + 1, minute_interval), 1))

    for minute in day_in_minute_interval_steps:
        print("\n")
        print("Minute: ", minute)
        simulation_day.start_charging_between_intervals()
        charging_bevs_last_interval = copy.deepcopy(simulation_day.charging_bevs_list.get_charging_bevs_list())
        bevs_with_charging_end_in_last_interval = copy.deepcopy(simulation_day.bevs_to_remove)
        simulation_day.stop_charging_between_intervals()
        available_solar_power = get_available_solar_power_linear_interpolated(solar_peak_power,
                                                                              minute + minute_interval / 2)
        print("Waiting BEVs: ", simulation_day.waiting_bevs_list.get_waiting_bevs_list())
        update_waiting_bevs_forecast(minute, simulation_day, simulation_data, available_solar_power)
        update_charging_bevs_from_post_optimization_plan(minute, simulation_day, minute_interval, available_solar_power,
                                                         solar_peak_power, simulation_data, bev_data)
        print("Waiting BEVs after updating parking end: ", simulation_day.waiting_bevs_list.get_waiting_bevs_list())
        print("Charging BEVs after updating post optimization plan and parking end: ",
              simulation_day.charging_bevs_list.get_charging_bevs_list())
        available_solar_power_last_interval = get_available_solar_power_linear_interpolated(solar_peak_power,
                                                                                            minute - minute_interval / 2)
        if minute != 480:
            update_charging_time(minute, simulation_day)
            update_fueled_solar_energy(available_solar_power_last_interval, simulation_day, minute_interval, minute,
                                       simulation_data, charging_bevs_last_interval,
                                       bevs_with_charging_end_in_last_interval)

        # Solar-Energie die im letzten, vergangenen Minuten-Intervall getankt wurde,
        # durch zwei sorgt für stückweise interpolation
        update_new_charging_bevs(solar_peak_power, minute, available_solar_power,
                                 charging_power_pro_bev, simulation_day, bev_data,
                                 simulation_data, minute_interval)
        print("Charging BEVs (nachdem neue Plätze belegt): ",
              simulation_day.charging_bevs_list.get_charging_bevs_list())
        for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
            parking_end = simulation_day.bevs_dict.get_parking_end_in_minutes(id_bev)
            residual_parking_time = parking_end - minute
            update_currently_charging_bevs(residual_parking_time, simulation_day, solar_peak_power, minute,
                                           minute_interval, simulation_data, bev_data,
                                           available_solar_power, id_bev)
        print("Charging BEVs: ", simulation_day.charging_bevs_list.get_charging_bevs_list())
        safe_charging_list_per_minute(simulation_day, simulation_data, minute)
        available_solar_power_start_of_interval = get_available_solar_power_linear_interpolated(solar_peak_power,
                                                                                                minute)
        safe_bev_dict_per_minute_forecast(minute, simulation_day, bev_data, table_dict, available_solar_power_start_of_interval)
    # das auch noch das Intervall bis 960 abgedeckt ist
    update_fueled_solar_energy_for_last_interval(solar_peak_power, simulation_day, minute_interval, simulation_data)


def init_simulation(day_in_minute_interval_steps, minute_interval, simulation_data, simulation_day, solar_peak_power):
    for minute in day_in_minute_interval_steps:
        available_solar_power = get_available_solar_power_linear_interpolated(solar_peak_power,
                                                                              minute + minute_interval / 2)
        update_waiting_bevs_forecast(minute, simulation_day, simulation_data, available_solar_power)
    set_fair_charging_energy(simulation_day, simulation_data, minute_interval)
    simulation_day.reset_simulation_day()


def update_charging_bevs_from_post_optimization_plan(minute, simulation_day, minute_interval, available_solar_power,
                                                     solar_peak_power, simulation_data, bev_data):
    for id_bev in simulation_day.bevs_dict.get_bevs_dict():
        if len(simulation_day.bevs_dict.get_charging_data(id_bev)) > 0:
            charging_start = simulation_day.bevs_dict.get_charging_start(id_bev)
            charging_end = simulation_day.bevs_dict.get_charging_end(id_bev)
            residual_charging_time = charging_end - minute
            if check_if_bev_charging_start_in_minute(minute, charging_start):
                add_charging_bev_from_optimization_plan(id_bev, simulation_day)
            if check_if_bev_charging_start_in_next_interval(minute, charging_start, minute_interval):
                simulation_day.bevs_dict.set_parking_state(id_bev, ParkingState.CHARGING)
                simulation_day.bevs_to_add_to_charging_list.append(id_bev)
            if check_if_bev_charging_end_in_minute(minute, charging_end):
                if id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
                    stop_charging(id_bev, simulation_day)
            if check_if_bev_charging_end_in_next_interval(residual_charging_time, minute_interval):
                if id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
                    number_of_charging_bevs = simulation_day.charging_bevs_list.get_number_of_charging_bevs()
                    solar_power_per_bev_for_next_interval = calculate_available_solar_power_per_bev(
                        available_solar_power,
                        number_of_charging_bevs)
                    swap_charging_bevs_because_residual_charging_time_over(residual_charging_time, id_bev,
                                                                           simulation_day,
                                                                           minute,
                                                                           solar_power_per_bev_for_next_interval,
                                                                           minute_interval, solar_peak_power,
                                                                           simulation_data,
                                                                           bev_data)


def check_if_bev_charging_start_in_minute(minute, charging_start):
    if minute == charging_start:
        return True
    return False


def get_number_of_bevs_with_charging_start_in_next_interval_from_post_optimization_plan(simulation_day, minute,
                                                                                        minute_interval):
    number_of_bevs_with_charging_start_in_next_interval = 0
    for id_bev in simulation_day.bevs_dict.get_bevs_dict():
        if len(simulation_day.bevs_dict.get_charging_data(id_bev)) > 0:
            charging_start = simulation_day.bevs_dict.get_charging_start(id_bev)
            if check_if_bev_charging_start_in_next_interval(minute, charging_start, minute_interval):
                number_of_bevs_with_charging_start_in_next_interval += 1
    return number_of_bevs_with_charging_start_in_next_interval


def check_if_bev_with_charging_start_in_next_interval_from_post_optimization_plan(simulation_day, minute,
                                                                                  minute_interval):
    for id_bev in simulation_day.bevs_dict.get_bevs_dict():
        if len(simulation_day.bevs_dict.get_charging_data(id_bev)) > 0:
            charging_start = simulation_day.bevs_dict.get_charging_start(id_bev)
            if check_if_bev_charging_start_in_next_interval(minute, charging_start, minute_interval):
                return True
    return False


def check_if_bev_charging_start_in_next_interval(minute, charging_start, minute_interval):
    if minute < charging_start < minute + minute_interval:
        return True
    return False


def check_if_bev_charging_end_in_minute(minute, charging_end):
    if minute == charging_end:
        return True
    return False


def check_if_bev_charging_end_in_next_interval(residual_charging_time, minute_interval):
    if 0 < residual_charging_time < minute_interval:
        return True
    return False


def save_charging_power_per_bev_for_current_minute(simulation_day, solar_peak_power, minute, id_bev, bev_data,
                                                   minute_interval):
    number_of_charging_bevs = simulation_day.charging_bevs_list.get_number_of_charging_bevs()
    # TODO Mitte von Intervall oder dann "falsche" Visualisation?
    available_solar_power = get_available_solar_power_linear_interpolated(solar_peak_power, minute + minute_interval/2)
    charging_power_real_per_bev = get_charging_power_per_bev(available_solar_power, number_of_charging_bevs)
    print("{} ID BEV: CHARGINNNNNNGGGGG POWER REAL: ".format(id_bev), charging_power_real_per_bev)
    bev_data.add_charging_power_per_bev_per_minute_dict(id_bev, minute, charging_power_real_per_bev)


# TODO ggf. falsch
def update_fueled_solar_energy_for_last_interval(solar_peak_power, simulation_day, minute_interval, simulation_data):
    minute = 960 + minute_interval
    simulation_day.start_charging_between_intervals()
    charging_bevs_last_interval = copy.deepcopy(simulation_day.charging_bevs_list.get_charging_bevs_list())
    bevs_with_charging_end_in_last_interval = copy.deepcopy(simulation_day.bevs_to_remove)
    simulation_day.stop_charging_between_intervals()
    available_solar_power_last_interval = get_available_solar_power_linear_interpolated(solar_peak_power, 960)
    update_fueled_solar_energy(available_solar_power_last_interval, simulation_day, minute_interval, minute,
                               simulation_data, charging_bevs_last_interval, bevs_with_charging_end_in_last_interval)


def set_fair_charging_energy(simulation_day, simulation_data, minute_interval):
    for id_bev in simulation_day.bevs_dict.get_bevs_dict().keys():
        fair_share_charging_energy = get_fair_share_charging_energy(simulation_day, id_bev, simulation_data,
                                                                    minute_interval)
        simulation_day.bevs_dict.add_fair_share_charging_energy(id_bev, fair_share_charging_energy)


def update_new_charging_bevs(solar_peak_power, minute, available_solar_power,
                             charging_power_pro_bev, simulation_day, bev_data,
                             simulation_data, minute_interval):
    update_charging_bevs_for_next_interval(available_solar_power, minute, charging_power_pro_bev, simulation_day,
                                           bev_data, simulation_data, minute_interval, solar_peak_power)
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        save_charging_power_per_bev_for_current_minute(simulation_day, solar_peak_power, minute, id_bev, bev_data,
                                                       minute_interval)


def update_currently_charging_bevs(residual_parking_time, simulation_day, solar_peak_power, minute, minute_interval,
                                   simulation_data, bev_data,
                                   available_solar_power, id_bev):
    number_of_charging_bevs = simulation_day.charging_bevs_list.get_number_of_charging_bevs()
    print("AVAILABLE SOLAR POWER: ", available_solar_power)
    solar_power_per_bev_for_next_interval = calculate_available_solar_power_per_bev(available_solar_power,
                                                                                    number_of_charging_bevs)
    update_residual_charging_time(simulation_day, solar_peak_power, minute, minute_interval, simulation_data,
                                  solar_power_per_bev_for_next_interval, bev_data, id_bev)
    stop_parking_if_less_than_next_interval(simulation_day, minute, minute_interval, solar_peak_power,
                                            solar_power_per_bev_for_next_interval, simulation_data, bev_data,
                                            residual_parking_time, id_bev)


def update_charging_bevs_for_next_interval(available_solar_power, minute, charging_power_pro_bev, simulation_day,
                                           bev_data, simulation_data, minute_interval, solar_peak_power):
    number_of_waiting_bevs = simulation_day.waiting_bevs_list.get_number_of_waiting_bevs()
    number_of_charging_bevs = get_number_of_charging_bevs(simulation_day)
    number_of_planned_bevs_from_post_optimization = \
        get_number_of_bevs_with_charging_start_in_next_interval_from_post_optimization_plan(
            simulation_day, minute, minute_interval)
    number_of_free_charging_stations = get_number_of_available_charging_stations(
        get_number_of_charging_stations(available_solar_power,
                                        charging_power_pro_bev), number_of_charging_bevs,
        number_of_planned_bevs_from_post_optimization)
    if check_if_free_charging_stations(number_of_free_charging_stations) and \
            check_if_new_bevs_for_charging(simulation_day):
        number_of_unoccupied_charging_stations = get_number_of_unoccupied_charging_stations(
            number_of_free_charging_stations, number_of_waiting_bevs)
        number_of_bevs_to_add = get_number_of_bevs_to_add(number_of_free_charging_stations,
                                                          number_of_unoccupied_charging_stations)
        add_charging_bevs(number_of_bevs_to_add, minute, simulation_day)
    elif check_if_free_charging_stations(number_of_free_charging_stations) is False and \
            check_if_new_bevs_for_charging(simulation_day):
        update_unused_solar_energy(solar_peak_power, minute, simulation_data, minute_interval)


def get_number_of_bevs_to_add(number_of_free_charging_stations, number_of_unoccupied_charging_stations):
    return number_of_free_charging_stations - number_of_unoccupied_charging_stations


def stop_parking_if_less_than_next_interval(simulation_day, current_minute, minute_interval, solar_peak_power,
                                            solar_power_per_bev_for_next_interval, simulation_data, bev_data,
                                            residual_parking_time, id_bev):
    parking_end = simulation_day.bevs_dict.get_parking_end_in_minutes(id_bev)
    if (current_minute + minute_interval) > parking_end > current_minute:
        update_because_parking_time_over(id_bev, residual_parking_time, simulation_day, current_minute,
                                         solar_power_per_bev_for_next_interval, solar_peak_power, simulation_data,
                                         bev_data, minute_interval)


def update_because_parking_time_over(id_bev, residual_parking_time, simulation_day, minute,
                                     solar_power_per_bev_for_next_interval,
                                     solar_peak_power, simulation_data, bev_data, minute_interval):
    print("Die Restparkzeit von BEV ", id_bev, "endet vor dem nächsten Intervall")
    set_bev_data_after_parking_time_over(id_bev, simulation_day, solar_power_per_bev_for_next_interval,
                                         residual_parking_time, minute, bev_data, solar_peak_power, minute_interval)
    stop_parking(id_bev, simulation_day)
    if check_if_bev_with_charging_start_in_next_interval_from_post_optimization_plan(simulation_day, minute,
                                                                                     minute_interval) is False:
        allocate_freed_solar_energy(bev_data, minute, minute_interval, residual_parking_time, simulation_data,
                                    simulation_day, solar_peak_power, solar_power_per_bev_for_next_interval)


# TODO hier statt stufen funktion Mitte vom Interval nehmen
def update_residual_charging_time(simulation_day, solar_peak_power, minute, minute_interval, simulation_data,
                                  solar_power_per_bev_for_next_interval, bev_data, id_bev):
    already_fueled_charging_energy = simulation_day.bevs_dict.get_fueled_charging_energy(id_bev)
    fair_share_charging_energy = simulation_day.bevs_dict.get_fair_share_charging_energy(id_bev)
    residual_charging_energy = get_residual_charging_energy(already_fueled_charging_energy,
                                                            fair_share_charging_energy)
    print("Restladeenergie bis zur fairen Ladeenergie for BEV mit ID {}: ".format(id_bev), residual_charging_energy)
    set_charging_end_if_less_than_next_interval(residual_charging_energy, solar_power_per_bev_for_next_interval,
                                                simulation_day, id_bev, minute_interval, solar_peak_power, minute,
                                                simulation_data, bev_data)


def set_charging_end_if_less_than_next_interval(residual_charging_energy, solar_power_per_bev_for_next_interval,
                                                simulation_day,
                                                id_bev, minute_interval, solar_peak_power, minute, simulation_data,
                                                bev_data):
    residual_charging_time = get_residual_charging_time(residual_charging_energy,
                                                        solar_power_per_bev_for_next_interval)
    print("Restladezeit: ", residual_charging_time)
    if check_if_charging_energy_less_than_next_interval(solar_power_per_bev_for_next_interval, minute_interval,
                                                        residual_charging_energy, id_bev) and \
            check_if_solar_power_per_bev_for_next_interval_is_not_null(solar_power_per_bev_for_next_interval):
        swap_charging_bevs_because_residual_charging_time_over(residual_charging_time, id_bev, simulation_day, minute,
                                                               solar_power_per_bev_for_next_interval, minute_interval,
                                                               solar_peak_power, simulation_data, bev_data)


def swap_charging_bevs_because_residual_charging_time_over(residual_charging_time, id_bev, simulation_day, minute,
                                                           solar_power_per_bev_for_next_interval,
                                                           minute_interval, solar_peak_power, simulation_data,
                                                           bev_data):
    print("Die Restladezeit des BEVS {} endet vor dem nächsten Interval".format(id_bev))
    set_bev_data_after_charging_time_over(residual_charging_time, id_bev, simulation_day, minute,
                                          solar_power_per_bev_for_next_interval, minute_interval, bev_data,
                                          solar_peak_power)
    stop_charging(id_bev, simulation_day)
    if check_if_bev_with_charging_start_in_next_interval_from_post_optimization_plan(simulation_day, minute,
                                                                                     minute_interval) is False:
        allocate_freed_solar_energy(bev_data, minute, minute_interval, residual_charging_time, simulation_data,
                                    simulation_day, solar_peak_power, solar_power_per_bev_for_next_interval)


# TODO hier noch einfügen ob BEVS from post optimization plan dran sind
def allocate_freed_solar_energy(bev_data, minute, minute_interval, residual_time, simulation_data,
                                simulation_day, solar_peak_power, solar_power_per_bev_for_next_interval):
    chosen_bev_to_start_charging = get_bev_to_start_charging(simulation_day, minute, residual_time)
    number_of_charging_bevs = simulation_day.charging_bevs_list.get_number_of_charging_bevs()
    print("Ausgewähltes BEV das frei gewordenen Platz belegen darf: ", chosen_bev_to_start_charging)
    if check_if_bev_on_waiting_list(chosen_bev_to_start_charging):
        simulation_day.prepare_charging_between_intervals(chosen_bev_to_start_charging)
        charging_start = minute + residual_time
        start_charging_of_new_bev(simulation_day, charging_start, chosen_bev_to_start_charging,
                                  solar_power_per_bev_for_next_interval, bev_data)
    if not check_if_bev_on_waiting_list(chosen_bev_to_start_charging) and \
            check_if_bev_on_charging_list(simulation_day):
        share_remaining_charging_power_per_bev(simulation_day, solar_power_per_bev_for_next_interval,
                                               residual_time, number_of_charging_bevs)
    if not check_if_bev_on_waiting_list(chosen_bev_to_start_charging) and not check_if_bev_on_charging_list(
            simulation_day):
        set_unused_solar_energy(residual_time, solar_peak_power, minute, minute_interval, simulation_data)


def set_bev_data_after_charging_time_over(residual_charging_time, id_bev, simulation_day, minute,
                                          solar_power_per_bev_for_next_interval, minute_interval, bev_data,
                                          solar_peak_power):
    charging_end = minute + residual_charging_time
    charging_start = simulation_day.bevs_dict.get_charging_start(id_bev)
    final_charging_time = get_final_charging_time(charging_start, charging_end)
    simulation_day.bevs_dict.set_charging_time(id_bev, final_charging_time)
    residual_solar_energy_till_charging_end = solar_power_per_bev_for_next_interval * (residual_charging_time / 60)
    simulation_day.bevs_dict.add_fueled_charging_energy(id_bev, residual_solar_energy_till_charging_end)
    save_charging_power_per_bev_for_current_minute(simulation_day, solar_peak_power, minute, id_bev, bev_data,
                                                   minute_interval)
    bev_data.add_charging_power_per_bev_per_minute_dict(id_bev, charging_end,
                                                        solar_power_per_bev_for_next_interval)


def get_final_charging_time(charging_start, charging_end):
    return charging_end - charging_start


# TODO solar power bei Abbruch korrekt berechnen
def set_bev_data_after_parking_time_over(id_bev, simulation_day, solar_power_per_bev_for_next_interval,
                                         residual_parking_time, minute, bev_data, solar_peak_power, minute_interval):
    residual_solar_energy_till_parking_end = solar_power_per_bev_for_next_interval * (residual_parking_time / 60)
    simulation_day.bevs_dict.add_fueled_charging_energy(id_bev, residual_solar_energy_till_parking_end)
    charging_end = minute + residual_parking_time
    charging_start = simulation_day.bevs_dict.get_charging_start(id_bev)
    final_charging_time = get_final_charging_time(charging_start, charging_end)
    simulation_day.bevs_dict.set_charging_time(id_bev, final_charging_time)
    save_charging_power_per_bev_for_current_minute(simulation_day, solar_peak_power, minute, id_bev, bev_data,
                                                   minute_interval)
    # * number_of_charging_bevs damit Wert in Diagramm gestapelt wird
    number_of_charging_bevs = simulation_day.charging_bevs_list.get_number_of_charging_bevs()
    bev_data.add_charging_power_per_bev_per_minute_dict(id_bev, charging_end,
                                                        solar_power_per_bev_for_next_interval)


def set_unused_solar_energy(residual_time, solar_peak_power, minute, minute_interval, simulation_data):
    unused_solar_energy_interval = residual_time
    unused_solar_power = get_available_solar_power_linear_interpolated(solar_peak_power, minute + minute_interval / 2)
    safe_unused_solar_energy(calculate_unused_solar_energy(unused_solar_power, unused_solar_energy_interval),
                             simulation_data)


def share_remaining_charging_power_per_bev(simulation_day, solar_power_per_bev_for_next_interval, residual_time,
                                           number_of_charging_bevs):
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        remaining_charging_power_per_bev = solar_power_per_bev_for_next_interval / number_of_charging_bevs
        charging_interval = residual_time
        new_charging_energy = calculate_new_charging_energy(remaining_charging_power_per_bev, charging_interval)
        simulation_day.bevs_dict.add_fueled_charging_energy(id_bev, new_charging_energy)


def start_charging_of_new_bev(simulation_day, charging_start, chosen_bev_to_start_charging,
                              solar_power_per_bev_for_next_interval, bev_data):
    print("Ladestart für ausgewähltes BEV: ", charging_start)
    simulation_day.init_charging_data(chosen_bev_to_start_charging, charging_start)
    # TODO hier berechnen wie hoch charging_power für Darstellung sein muss ?!
    print("{} CHARGING POWER WIRD FÜR NEUES BEV {} GESPEICHERT: ".format(solar_power_per_bev_for_next_interval,
                                                                         chosen_bev_to_start_charging))
    print("ZEITPUNKT FÜR DAS ES GESPEICHERT WIRD: ", charging_start)
    bev_data.add_charging_power_per_bev_per_minute_dict(chosen_bev_to_start_charging, charging_start,
                                                        solar_power_per_bev_for_next_interval)


def get_bev_to_start_charging(simulation_day, minute, residual_charging_time):
    for id_bev in simulation_day.waiting_bevs_list.get_waiting_bevs_list():
        parking_end = simulation_day.bevs_dict.get_parking_end_in_minutes(id_bev)
        residual_parking_time = parking_end - minute
        if residual_parking_time > residual_charging_time:
            return id_bev


def get_fair_share_charging_energy(simulation_day, id_bev, simulation_data, minute_interval):
    available_solar_power_per_bev_in_parking_interval_dict = OrderedDict(sorted(
        get_available_solar_power_in_parking_interval_dict(
            simulation_day, id_bev, simulation_data, minute_interval).items()))
    return calculate_fair_share_charging_energy(available_solar_power_per_bev_in_parking_interval_dict,
                                                minute_interval)
