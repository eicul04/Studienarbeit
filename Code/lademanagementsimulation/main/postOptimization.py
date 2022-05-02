from collections import OrderedDict

from data import get_available_solar_power
from distributionAlgorithmForecastPolling import get_fair_share_charging_energy, update_charging_bevs, \
    update_fueled_solar_energy_for_last_interval

# Nachoptimierungslauf:
# Aufträge nach Abfahrtzeit absteigend sortieren
# d.h. zuerst den Auftrag der als letzter das Parkhaus verlässt.
# Dann terminieren Sie diese rückwärts (d.h. Verfahren läuft spiegelverkehrt).
# Dadurch wird z.B. Ihr Auftrag 5 auf den Nachmittag verschoben und auf die Prognosezeit verkürzt.
# Es ist eine Nachoptimierung, da jedes bereits eingeplante BEV seine
# prognostizierte Energie behalten darf und zulässig nach hinten geschoben wird
from simulateDay import safe_simulation_day_state
from simulateDayForecast import simulate_day_forecast
from simulationData import safe_charging_list_per_minute, safe_bev_dict_per_minute_forecast
from simulationService import update_fueled_solar_energy
from timeTransformation import in_minutes


def start_post_optimization(minute_interval, simulation_day, solar_peak_power, bev_data, table_dict, simulation_data,
                            charging_power_pro_bev):
    print("START POST OPTIMIZATION")
    sort_waiting_list_descending_by_parking_end(simulation_day)
    day_in_minute_interval_steps = list(reversed(range(480, 960 + 1, minute_interval)))
    for minute in day_in_minute_interval_steps:
        print("\n")
        print("Minute: ", minute)
        simulation_day.start_charging_between_intervals()
        simulation_day.stop_charging_between_intervals()
        update_because_parking_time_over(minute, simulation_day, bev_data, table_dict, solar_peak_power,
                                         simulation_data, minute_interval)
        print("Charging BEVs: ", simulation_day.charging_bevs_list.get_charging_bevs_list())
        print("Waiting BEVs: ", simulation_day.waiting_bevs_list.get_waiting_bevs_list())
        available_solar_power_last_interval = get_available_solar_power(solar_peak_power, minute - minute_interval / 2)
        if minute != 960:
            update_fueled_solar_energy(available_solar_power_last_interval, simulation_day, minute_interval, minute,
                                       simulation_data)
        update_charging_bevs(solar_peak_power, minute, charging_power_pro_bev, simulation_day, bev_data,
                             simulation_data, minute_interval)
        print("Charging BEVs: ", simulation_day.charging_bevs_list.get_charging_bevs_list())
        safe_charging_list_per_minute(simulation_day, simulation_data, minute)
        safe_bev_dict_per_minute_forecast(minute, simulation_day, bev_data, table_dict, solar_peak_power)


def update_charging_bevs(solar_peak_power, minute,
                         charging_power_pro_bev, simulation_day, bev_data,
                         simulation_data, minute_interval):
    available_solar_power = get_available_solar_power(solar_peak_power, minute - minute_interval / 2)
    update_charging_bevs_for_next_interval(available_solar_power, minute, charging_power_pro_bev, simulation_day,
                                           bev_data, simulation_data, minute_interval, solar_peak_power)
    number_of_charging_bevs = simulation_day.charging_bevs_list.get_number_of_charging_bevs()
    print("Charging BEVs list before saving: ", simulation_day.charging_bevs_list.get_charging_bevs_list())
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        save_charging_power_per_bev_for_current_minute(simulation_day, solar_peak_power, minute, id_bev, bev_data,
                                                       minute_interval)
    update_residual_charging_time(simulation_day, solar_peak_power, minute, minute_interval, simulation_data,
                                  number_of_charging_bevs, bev_data)
    stop_parking_if_less_than_next_interval(simulation_day, minute, minute_interval, solar_peak_power,
                                            number_of_charging_bevs, simulation_data, bev_data)



def update_because_parking_time_over(minute, simulation_day, bev_data, table_dict, solar_peak_power, simulation_data,
                                     minute_interval):
    update_bevs_in_waiting_bevs_list(minute, simulation_day.waiting_bevs_list,
                                     simulation_day)
    update_bevs_in_charging_bevs_list_if_parking_start_in_minute(minute, simulation_day.charging_bevs_list,
                                                                 simulation_day)
    safe_simulation_day_state(minute, simulation_day, bev_data, table_dict, solar_peak_power, simulation_data,
                              minute_interval)


# TODO Methode auf parking_start anpassen
def update_bevs_in_waiting_bevs_list(current_minute, waiting_bevs_list, simulation_day):
    for id_bev in waiting_bevs_list.get_waiting_bevs_list():
        parking_start = in_minutes(simulation_day.bevs_dict.get_parking_start(id_bev))
        if parking_start <= current_minute:
            print("STOP PARKING BEV {} from waiting list".format(id_bev))
            simulation_day.stop_parking(id_bev)
    simulation_day.remove_from_list(waiting_bevs_list)


def update_bevs_in_charging_bevs_list_if_parking_start_in_minute(current_minute, charging_bevs_list, simulation_day):
    for id_bev in charging_bevs_list.get_charging_bevs_list():
        parking_start = in_minutes(simulation_day.bevs_dict.get_parking_start(id_bev))
        if parking_start == current_minute:
            print("STOP PARKING BEV {} from charging list".format(id_bev))
            simulation_day.stop_parking(id_bev)
    simulation_day.remove_from_list(charging_bevs_list)


def set_charging_start_if_fair_share_charging_energy_reached(simulation_day, simulation_data, minute_interval):
    for id_bev in get_sorted_descending_bev_id_with_parking_end_dict(simulation_day):
        fair_share_charging_energy = get_fair_share_charging_energy(simulation_day, id_bev, simulation_data,
                                                                    minute_interval)
        # Minuten Intervalle rückwärts von Parking end ablaufen und schauen wann fair_share_charging_energy erreicht,
        # wenn erreicht dann setzte charging start


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
