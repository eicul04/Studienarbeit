from collections import OrderedDict

from calculation import get_available_solar_power_linear_interpolated, calculate_available_solar_power_per_bev
from distributionAlgorithmForecastPolling import get_fair_share_charging_energy, update_new_charging_bevs, \
    update_fueled_solar_energy_for_last_interval, update_currently_charging_bevs, \
    check_if_charging_energy_less_than_next_interval, start_charging_of_new_bev, share_remaining_charging_power_per_bev, \
    set_unused_solar_energy
from simulationClasses import ParkingState
from simulationData import safe_charging_list_per_minute, safe_bev_dict_per_minute_forecast
from simulationService import update_fueled_solar_energy, get_residual_charging_energy, \
    get_residual_charging_time, check_if_solar_power_per_bev_for_next_interval_is_not_null, stop_charging, \
    check_if_bev_on_waiting_list, check_if_bev_on_charging_list, get_charging_power_per_bev, \
    calculate_new_charging_energy
from timeTransformation import in_minutes


# Nachoptimierungslauf:
# Aufträge nach Abfahrtzeit absteigend sortieren
# d.h. zuerst den Auftrag der als letzter das Parkhaus verlässt.
# Dann terminieren Sie diese rückwärts (d.h. Verfahren läuft spiegelverkehrt).
# Dadurch wird z.B. Ihr Auftrag 5 auf den Nachmittag verschoben und auf die Prognosezeit verkürzt.
# Es ist eine Nachoptimierung, da jedes bereits eingeplante BEV seine
# prognostizierte Energie behalten darf und zulässig nach hinten geschoben wird
# TODO nach Durchlauf einfach charging end als charging start setzen und dann nochmal normal durchlaufen lassen
def start_post_optimization(minute_interval, simulation_day, solar_peak_power, bev_data, table_dict, simulation_data,
                            charging_power_pro_bev):
    print("START POST OPTIMIZATION")
    simulation_day.reset_simulation_day()
    if_parking_end_out_of_simulation_set_to_interval_max(simulation_day)
    day_in_minute_interval_steps = list(reversed(range(480, 960 + 1, minute_interval)))
    for minute in day_in_minute_interval_steps:
        simulation_day.start_charging_between_intervals()
        simulation_day.stop_charging_between_intervals()
        add_bevs_to_waiting_list_if_parking_end_equals_current_minute(simulation_day, minute)
        available_solar_power = get_available_solar_power_linear_interpolated(solar_peak_power,
                                                                              minute - minute_interval / 2)
        # TODO ob folgende Methode sinn macht??
        update_because_parking_time_over_optimization(minute, simulation_day, available_solar_power, simulation_data)
        available_solar_power_last_interval = get_available_solar_power_linear_interpolated(solar_peak_power,
                                                                                            minute + minute_interval / 2)
        if minute < 960:
            update_fueled_solar_energy_optimization(available_solar_power_last_interval, simulation_day,
                                                    minute_interval,
                                                    minute, simulation_data)
            update_charging_time_optimization(minute, simulation_day)
        update_new_charging_bevs(solar_peak_power, minute, available_solar_power,
                                 charging_power_pro_bev, simulation_day, bev_data,
                                 simulation_data, minute_interval)
        for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
            parking_start = simulation_day.bevs_dict.get_parking_start(id_bev)
            residual_parking_time = parking_start - minute
            update_currently_charging_bevs_optimization(residual_parking_time, simulation_day, solar_peak_power, minute,
                                                        minute_interval, simulation_data, bev_data,
                                                        available_solar_power, id_bev)
        safe_charging_list_per_minute(simulation_day, simulation_data, minute)
        # safe_bev_dict_per_minute_forecast(minute, simulation_day, bev_data, table_dict, available_solar_power)
    remove_charging_data_if_charging_time_zero(simulation_day)
    set_bevs_dict_charging_start_for_forward_pass(simulation_day)
    clear_charging_energy(simulation_day)
    print("\n")
    print("OPTIMIZATION DONE")
    print("BEVs dict: ", simulation_day.bevs_dict.get_bevs_dict())


def set_bevs_dict_charging_start_for_forward_pass(simulation_day):
    for id_bev in simulation_day.bevs_dict.get_bevs_dict():
        charging_start_from_backward_pass = simulation_day.bevs_dict.get_charging_start(id_bev)
        charging_time = simulation_day.bevs_dict.get_charging_time(id_bev)
        if charging_start_from_backward_pass is not None and charging_time is not None:
            new_charging_start = charging_start_from_backward_pass - charging_time
            simulation_day.bevs_dict.set_charging_start(id_bev, new_charging_start)


def clear_charging_energy(simulation_day):
    for id_bev in simulation_day.bevs_dict.get_bevs_dict():
        if len(simulation_day.bevs_dict.get_charging_data(id_bev)) > 0:
            simulation_day.bevs_dict.set_charging_energy(id_bev, 0)


def remove_charging_data_if_charging_time_zero(simulation_day):
    for id_bev in simulation_day.bevs_dict.get_bevs_dict():
        if len(simulation_day.bevs_dict.get_charging_data(id_bev)) > 0:
            charging_time = simulation_day.bevs_dict.get_charging_time(id_bev)
            if charging_time == 0:
                simulation_day.bevs_dict.remove_charging_data(id_bev)


def update_fueled_solar_energy_optimization(available_solar_power_last_interval, simulation_day, minute_interval,
                                            minute,
                                            simulation_data):
    # Number of charging bevs für das letzte Intervall bekommen
    last_interval = minute + minute_interval
    number_of_charging_bevs_of_last_interval = len(simulation_data.charging_list_per_minute_dict[last_interval])
    if number_of_charging_bevs_of_last_interval != 0:
        charging_power_per_bev = get_charging_power_per_bev(available_solar_power_last_interval,
                                                            number_of_charging_bevs_of_last_interval)
        for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
            charging_time = get_charging_time_for_bev_in_charging_list(simulation_day, minute, id_bev)
            if charging_time % minute_interval == 0:
                new_charging_energy = calculate_new_charging_energy(charging_power_per_bev, minute_interval)
                simulation_day.bevs_dict.add_fueled_charging_energy(id_bev, new_charging_energy)
            else:
                charging_interval = charging_time % minute_interval
                new_charging_energy = calculate_new_charging_energy(charging_power_per_bev, charging_interval)
                simulation_day.bevs_dict.add_fueled_charging_energy(id_bev, new_charging_energy)


def update_currently_charging_bevs_optimization(residual_parking_time, simulation_day, solar_peak_power, minute,
                                                minute_interval,
                                                simulation_data, bev_data,
                                                available_solar_power, id_bev):
    number_of_charging_bevs = simulation_day.charging_bevs_list.get_number_of_charging_bevs()
    solar_power_per_bev_for_next_interval = calculate_available_solar_power_per_bev(available_solar_power,
                                                                                    number_of_charging_bevs)
    update_residual_charging_time_optimization(simulation_day, solar_peak_power, minute, minute_interval,
                                               simulation_data,
                                               solar_power_per_bev_for_next_interval, bev_data, id_bev)
    stop_parking_if_less_than_next_interval_optimization(simulation_day, minute, minute_interval, minute,
                                                         available_solar_power, simulation_data, id_bev)


def stop_parking_if_less_than_next_interval_optimization(simulation_day, current_minute, minute_interval, minute,
                                                         available_solar_power, simulation_data, id_bev):
    parking_end = simulation_day.bevs_dict.get_parking_end_in_minutes(id_bev)
    if (current_minute + minute_interval) > parking_end > current_minute:
        update_because_parking_time_over_optimization(minute, simulation_day, available_solar_power, simulation_data)


def update_residual_charging_time_optimization(simulation_day, solar_peak_power, minute, minute_interval,
                                               simulation_data,
                                               solar_power_per_bev_for_next_interval, bev_data, id_bev):
    already_fueled_charging_energy = simulation_day.bevs_dict.get_fueled_charging_energy(id_bev)
    fair_share_charging_energy = simulation_day.bevs_dict.get_fair_share_charging_energy(id_bev)
    residual_charging_energy = get_residual_charging_energy(already_fueled_charging_energy,
                                                            fair_share_charging_energy)
    set_charging_end_if_less_than_next_interval_optimization(residual_charging_energy,
                                                             solar_power_per_bev_for_next_interval,
                                                             simulation_day, id_bev, minute_interval, solar_peak_power,
                                                             minute,
                                                             simulation_data, bev_data)


def set_charging_end_if_less_than_next_interval_optimization(residual_charging_energy,
                                                             solar_power_per_bev_for_next_interval,
                                                             simulation_day,
                                                             id_bev, minute_interval, solar_peak_power, minute,
                                                             simulation_data,
                                                             bev_data):
    residual_charging_time = get_residual_charging_time(residual_charging_energy,
                                                        solar_power_per_bev_for_next_interval)
    if check_if_charging_energy_less_than_next_interval(solar_power_per_bev_for_next_interval, minute_interval,
                                                        residual_charging_energy, id_bev) and \
            check_if_solar_power_per_bev_for_next_interval_is_not_null(solar_power_per_bev_for_next_interval):
        swap_charging_bevs_because_residual_charging_time_over_optimization(residual_charging_time, id_bev,
                                                                            simulation_day, minute,
                                                                            solar_power_per_bev_for_next_interval,
                                                                            minute_interval,
                                                                            solar_peak_power, simulation_data, bev_data)


def swap_charging_bevs_because_residual_charging_time_over_optimization(residual_charging_time, id_bev, simulation_day,
                                                                        minute,
                                                                        solar_power_per_bev_for_next_interval,
                                                                        minute_interval, solar_peak_power,
                                                                        simulation_data,
                                                                        bev_data):
    set_bev_data_after_charging_time_over_optimization(residual_charging_time, id_bev, simulation_day, minute,
                                                       solar_power_per_bev_for_next_interval, minute_interval, bev_data,
                                                       solar_peak_power)
    stop_charging(id_bev, simulation_day)
    allocate_freed_solar_energy_optimization(bev_data, minute, minute_interval, residual_charging_time, simulation_data,
                                             simulation_day, solar_peak_power, solar_power_per_bev_for_next_interval)


def allocate_freed_solar_energy_optimization(bev_data, minute, minute_interval, residual_charging_time, simulation_data,
                                             simulation_day, solar_peak_power, solar_power_per_bev_for_next_interval):
    chosen_bev_to_start_charging = get_bev_to_start_charging_optimization(
        simulation_day, minute, residual_charging_time)
    number_of_charging_bevs = simulation_day.charging_bevs_list.get_number_of_charging_bevs()
    if check_if_bev_on_waiting_list(chosen_bev_to_start_charging):
        simulation_day.prepare_charging_between_intervals(chosen_bev_to_start_charging)
        charging_start = minute - residual_charging_time
        start_charging_of_new_bev_optimization(simulation_day, charging_start, chosen_bev_to_start_charging,
                                               solar_power_per_bev_for_next_interval, bev_data)
    if not check_if_bev_on_waiting_list(chosen_bev_to_start_charging) and check_if_bev_on_charging_list(simulation_day):
        share_remaining_charging_power_per_bev(simulation_day, solar_power_per_bev_for_next_interval,
                                               residual_charging_time, number_of_charging_bevs)
    if not check_if_bev_on_waiting_list(chosen_bev_to_start_charging) and not check_if_bev_on_charging_list(
            simulation_day):
        set_unused_solar_energy(residual_charging_time, solar_peak_power, minute, minute_interval, simulation_data)


def start_charging_of_new_bev_optimization(simulation_day, charging_start, chosen_bev_to_start_charging,
                                           solar_power_per_bev_for_next_interval, bev_data):
    simulation_day.overwrite_charging_data(chosen_bev_to_start_charging, charging_start)
    bev_data.add_charging_power_per_bev_per_minute_dict(chosen_bev_to_start_charging, charging_start,
                                                        solar_power_per_bev_for_next_interval)


def get_bev_to_start_charging_optimization(simulation_day, minute, residual_charging_time):
    for id_bev in simulation_day.waiting_bevs_list.get_waiting_bevs_list():
        parking_start = simulation_day.bevs_dict.get_parking_start_in_minutes(id_bev)
        residual_parking_time = minute - parking_start
        if residual_parking_time > residual_charging_time:
            return id_bev


def set_bev_data_after_charging_time_over_optimization(residual_charging_time, id_bev, simulation_day, minute,
                                                       solar_power_per_bev_for_next_interval, minute_interval, bev_data,
                                                       solar_peak_power):
    charging_end = minute - residual_charging_time
    charging_start = simulation_day.bevs_dict.get_charging_start(id_bev)
    final_charging_time = get_final_charging_time_optimization(charging_start, charging_end)
    simulation_day.bevs_dict.set_charging_time(id_bev, final_charging_time)
    residual_solar_energy_till_charging_end = solar_power_per_bev_for_next_interval * (residual_charging_time / 60)
    simulation_day.bevs_dict.add_fueled_charging_energy(id_bev, residual_solar_energy_till_charging_end)
    # save_charging_power_per_bev_for_current_minute(simulation_day, solar_peak_power, minute, id_bev, bev_data,
    # minute_interval)
    bev_data.add_charging_power_per_bev_per_minute_dict(id_bev, charging_end,
                                                        solar_power_per_bev_for_next_interval)


def if_parking_end_out_of_simulation_set_to_interval_max(simulation_day):
    for id_bev in simulation_day.bevs_dict.get_bevs_dict().keys():
        parking_end = simulation_day.bevs_dict.get_parking_end_in_minutes(id_bev)
        if check_if_parking_end_out_of_simulation(parking_end):
            parking_start = simulation_day.bevs_dict.get_parking_start(id_bev)
            parking_time = 960 / 60 - parking_start
            simulation_day.bevs_dict.set_parking_time(id_bev, parking_time)


def check_if_parking_end_out_of_simulation(parking_end):
    if parking_end > 960:
        return True
    return False


def get_final_charging_time_optimization(charging_start, charging_end):
    return charging_start - charging_end


def update_charging_time_optimization(minute, simulation_day):
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        charging_time = get_charging_time_for_bev_in_charging_list(simulation_day, minute, id_bev)
        simulation_day.bevs_dict.set_charging_time(id_bev, charging_time)


def get_charging_time_for_bev_in_charging_list(simulation_day, minute, id_bev):
    charging_start = simulation_day.bevs_dict.get_charging_start(id_bev)
    if charging_start is not None:
        return charging_start - minute
    return 0


def add_bevs_to_waiting_list_if_parking_end_equals_current_minute(simulation_day, minute):
    for id_bev in simulation_day.bevs_dict.get_keys():
        parking_end = simulation_day.bevs_dict.get_parking_end_in_minutes(id_bev)
        if parking_end == minute:
            simulation_day.waiting_bevs_list.add_bev(id_bev)
            simulation_day.bevs_dict.set_parking_state(id_bev, ParkingState.WAITING)


def update_because_parking_time_over_optimization(minute, simulation_day, available_solar_power, simulation_data):
    update_bevs_in_waiting_bevs_list_optimization(minute, simulation_day.waiting_bevs_list,
                                                  simulation_day)
    update_bevs_in_charging_bevs_list_if_parking_start_in_minute_optimization(minute, simulation_day.charging_bevs_list,
                                                                              simulation_day)
    # safe_simulation_day_state(minute, simulation_day, simulation_data, available_solar_power)


def update_bevs_in_waiting_bevs_list_optimization(current_minute, waiting_bevs_list, simulation_day):
    for id_bev in waiting_bevs_list.get_waiting_bevs_list():
        parking_start = simulation_day.bevs_dict.get_parking_start_in_minutes(id_bev)
        if parking_start >= current_minute:
            simulation_day.stop_parking(id_bev)
    simulation_day.remove_from_list(waiting_bevs_list)


def update_bevs_in_charging_bevs_list_if_parking_start_in_minute_optimization(current_minute, charging_bevs_list,
                                                                              simulation_day):
    for id_bev in charging_bevs_list.get_charging_bevs_list():
        parking_start = in_minutes(simulation_day.bevs_dict.get_parking_start(id_bev))
        if parking_start == current_minute:
            simulation_day.stop_parking(id_bev)
    simulation_day.remove_from_list(charging_bevs_list)


def set_charging_start_if_fair_share_charging_energy_reached(simulation_day, simulation_data, minute_interval):
    for id_bev in get_sorted_descending_bev_id_with_parking_end_dict(simulation_day):
        fair_share_charging_energy = get_fair_share_charging_energy(simulation_day, id_bev, simulation_data,
                                                                    minute_interval)
        # Minuten Intervalle rückwärts von Parking end ablaufen und schauen wann fair_share_charging_energy erreicht,
        # wenn erreicht dann setzte charging start


# TODO delete methods below
def sort_waiting_list_descending_by_parking_end(simulation_day):
    sorted_descending_bev_id_with_parking_end_dict = get_sorted_descending_bev_id_with_parking_end_dict(simulation_day)
    for id_bev in sorted_descending_bev_id_with_parking_end_dict.keys():
        simulation_day.waiting_bevs_list.add_bev(id_bev)


def get_sorted_descending_bev_id_with_parking_end_dict(simulation_day):
    bev_id_with_parking_end_dict = {}
    for id_bev in simulation_day.bevs_dict.get_bevs_dict().keys():
        parking_end = simulation_day.bevs_dict.get_parking_end_in_minutes(id_bev)
        if parking_end > 960:
            bev_id_with_parking_end_dict[id_bev] = 960
        bev_id_with_parking_end_dict[id_bev] = parking_end
    sorted_parking_end_list = sorted(bev_id_with_parking_end_dict.items(), key=lambda kv: kv[1])
    sorted_parking_end_list.reverse()
    sorted_descending_bev_id_with_parking_end_dict = OrderedDict(sorted_parking_end_list)
    print(sorted_descending_bev_id_with_parking_end_dict)
    return sorted_descending_bev_id_with_parking_end_dict
