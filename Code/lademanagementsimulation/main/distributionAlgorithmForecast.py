import copy
from collections import OrderedDict

import numpy as np

from data import get_available_solar_power
from forecastCalculation import get_parking_start, get_parking_end, get_available_solar_power_in_parking_interval_dict, \
    calculate_fair_share_charging_energy
from simulateDay import simulate_day
from simulationData import safe_charging_list_per_minute, safe_bev_dict_per_minute_forecast
from simulationService import calculate_parking_end, calculate_number_of_charging_stations, calculate_charging_end, \
    get_charging_power_per_bev, update_charging_time, update_fueled_solar_energy

# für ankommendes BEV Prognose berechnen
# für alle anderen BEVs (außer für aufgeladene BEVs) Prognose anpassen
# Störfunktion: Abweichung zum prognostizierten Tagesverlauf der BEVs erzielen
# Störfunktion ändert parking_data

# keine maximale Ladezeit -> Ladezeit wird über Prognose berechnet
# zuerst zur Vereinfachung: ich weiß wann BEVs parken und ich weiß wann wie viel verfügbarer Solarstrom
# ich teile den BEVs die Ladeintervalle so zu, das alle möglichst gleich viel Solarstrom am Ende getankt haben
# aus den Ladeintervallen erstelle ich dann eine Ladeliste

# SimulationData = SimulationDataPrognose
# SimulationDataReal = SimulationDataPrognose + Störfunktion

from timeTransformation import in_minutes


def start_algorithm(simulation_data, simulation_day, maximum_charging_time, solar_peak_power,
                    bev_data, table_dict, charging_power_per_bev, minute_interval):
    day_in_minute_interval_steps = list(np.around(np.arange(480, 960 + 1, minute_interval), 1))
    for minute in day_in_minute_interval_steps:
        init_simulation_data(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data, minute_interval)
    simulation_day.reset_simulation_day()
    determine_charging_distribution(charging_power_per_bev, maximum_charging_time, simulation_data, simulation_day,
                                    solar_peak_power, minute_interval, bev_data)
    # update charging_times bei Veränderungen zum ursprünglichen Plan (bevs_dict Parkzeiten)
    # update immer für wartende und noch nicht parkende autos
    for minute in day_in_minute_interval_steps:
        simulate_day(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data)
        # TODO Tabellenerzeugung (fig nach hinten anschieben)
        safe_bev_dict_per_minute_forecast(minute, simulation_day, bev_data, table_dict, solar_peak_power)
        update_charging_bevs(minute, simulation_day)
        available_solar_power = get_available_solar_power(solar_peak_power, minute)
        update_fueled_solar_energy(available_solar_power, simulation_day, minute_interval, minute)
        for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
            number_of_charging_bevs = simulation_day.charging_bevs_list.get_number_of_charging_bevs()
            charging_power_real_per_bev = get_charging_power_per_bev(available_solar_power, number_of_charging_bevs)
            bev_data.add_charging_power_per_bev_per_minute_dict(id_bev, minute, charging_power_real_per_bev)
        safe_charging_list_per_minute(simulation_day, simulation_data, minute)


def update_charging_bevs(minute, simulation_day):
    # update_charging_time(minute, simulation_day)
    update_because_charging_time_starts(minute, simulation_day)
    update_because_charging_time_over(minute, simulation_day)


def update_because_charging_time_starts(current_minute, simulation_day):
    for id_bev in simulation_day.bevs_dict.get_bevs_dict():
        charging_start = simulation_day.bevs_dict.get_charging_start(id_bev)
        if current_minute == charging_start:
            simulation_day.start_charging(id_bev)


def update_because_charging_time_over(current_minute, simulation_day):
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        charging_start = simulation_day.bevs_dict.get_charging_start(id_bev)
        charging_time = simulation_day.bevs_dict.get_charging_time(id_bev)
        charging_end = charging_start + charging_time
        if current_minute >= charging_end:
            simulation_day.stop_charging(id_bev)
    simulation_day.remove_from_list(simulation_day.charging_bevs_list)


def determine_charging_distribution(charging_power_per_bev, maximum_charging_time, simulation_data, simulation_day,
                                    solar_peak_power, minute_interval, bev_data):
    print("Start: BEVs_dict", simulation_day.bevs_dict.get_bevs_dict())
    for id_bev in simulation_day.bevs_dict.get_bevs_dict().keys():
        #print("Updated BEVs_dict", simulation_day.bevs_dict.get_bevs_dict())
        #print("\n")
        #print("für BEV mit ID", id_bev)
        available_solar_power_per_bev_in_parking_interval_dict = OrderedDict(sorted(
            get_available_solar_power_in_parking_interval_dict(
                simulation_day, id_bev, simulation_data, minute_interval).items()))
        fair_share = calculate_fair_share_charging_energy(available_solar_power_per_bev_in_parking_interval_dict, minute_interval)
        #print(fair_share, "Fairer Anteil für BEV")
        forecast_dict = get_forecast_dict(id_bev, charging_power_per_bev, solar_peak_power, simulation_day,
                                          minute_interval)
        set_initial_charging_times(simulation_day, id_bev, fair_share, forecast_dict, bev_data)


def init_simulation_data(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data, minute_interval):
    simulate_day(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data, minute_interval)


def set_initial_charging_times(simulation_day, id_bev, fair_share, forecast_dict, bev_data):
    possible_charging_intervals_list = get_possible_charging_intervals_list(forecast_dict)
    if any(possible_charging_intervals_list):
        charging_energies_dict = get_charging_energies_dict(forecast_dict, possible_charging_intervals_list)
        highest_charging_energy = get_highest_charging_energy(charging_energies_dict)
        charging_interval_with_highest_charging_energy_as_list = get_charging_interval_with_highest_charging_energy(
            charging_energies_dict,
            possible_charging_intervals_list)
        charging_interval_as_list = shorten_charging_interval_if_more_than_fair_share(
            highest_charging_energy, charging_interval_with_highest_charging_energy_as_list,
            forecast_dict, fair_share)
        charging_interval = create_charging_interval(charging_interval_as_list)
        charging_energy = get_charging_energy_data(highest_charging_energy, fair_share, forecast_dict,
                                                   charging_interval_as_list)
        set_charging_data(id_bev, simulation_day, charging_interval[0], charging_interval[1])
        set_charging_energy_data(simulation_day, id_bev, fair_share, charging_energy)
    else:
        print("No charging slot available")
        bev_data.increase_number_of_bev_with_no_charging_slot_in_forecast()
        # TODO Was machen wenn kein charging slot frei?


# TODO delete 1. Ansatz um Maximum rumtanken?
# minute_when_max_available_solar_power_per_bev = get_minute_when_max_available_solar_power_per_bev(
#  available_solar_power_per_bev_in_parking_interval_dict)
# charging_start = get_charging_start(minute_when_max_available_solar_power_per_bev, maximum_charging_time)
# charging_end = get_charging_end(minute_when_max_available_solar_power_per_bev, maximum_charging_time)


def shorten_charging_interval_if_more_than_fair_share(highest_charging_energy,
                                                      charging_interval_with_highest_charging_energy_as_list,
                                                      forecast_dict, fair_share):
    if highest_charging_energy > fair_share:
        shortened_charging_interval_as_list = shorten_charging_interval_till_fit_fair_share(
            charging_interval_with_highest_charging_energy_as_list, forecast_dict, fair_share)
        return shortened_charging_interval_as_list
    else:
        return charging_interval_with_highest_charging_energy_as_list


def get_charging_energy_data(highest_charging_energy, fair_share, forecast_dict, shortened_charging_interval_as_list):
    if highest_charging_energy > fair_share:
        fair_charging_energy = get_fair_charging_energy(forecast_dict, shortened_charging_interval_as_list)
        return fair_charging_energy
    else:
        return highest_charging_energy


def get_minute_when_max_available_solar_power_per_bev(available_solar_power_per_bev_in_parking_interval_dict):
    return max(available_solar_power_per_bev_in_parking_interval_dict,
               key=available_solar_power_per_bev_in_parking_interval_dict.get)


def get_max_available_solar_power_per_bev(available_solar_power_per_bev_in_parking_interval_dict):
    return max(available_solar_power_per_bev_in_parking_interval_dict.values())


def get_charging_start(minute_when_max_available_solar_power_per_bev, maximum_charging_time):
    return int(minute_when_max_available_solar_power_per_bev - (maximum_charging_time / 2))


def get_charging_end(minute_when_max_available_solar_power_per_bev, maximum_charging_time):
    return int(minute_when_max_available_solar_power_per_bev + (maximum_charging_time / 2))


# TODO Abfrage, das maximal so viele in charging intervall wie available_charging_stations
def set_charging_data(id_bev, simulation_day, charging_start, charging_end):
    charging_time = charging_end - charging_start
    simulation_day.bevs_dict.add_charging_data_for_forecast(id_bev, charging_start, charging_time)


def get_fair_charging_energy(forecast_dict, shortened_charging_interval_as_list):
    last_minute = shortened_charging_interval_as_list[-1]
    fair_charging_energy = 0
    for minute in forecast_dict.keys():
        if minute <= last_minute + 1:
            fair_charging_energy += forecast_dict[minute][1]
    return fair_charging_energy


def set_charging_energy_data(simulation_day, id_bev, fair_share_charging_energy, forecast_charging_energy):
    simulation_day.bevs_dict.add_fair_share_charging_energy(id_bev, fair_share_charging_energy)


def create_charging_interval(charging_interval_as_list):
    charging_start = charging_interval_as_list[0]
    charging_end = charging_interval_as_list[-1]
    charging_interval = (charging_start, charging_end)
    return charging_interval


# TODO alle Parkingintervalle auf Ende beschränken? also 16 Uhr?
def get_forecast_dict(id_bev, charging_power_per_bev, solar_peak_power, simulation_day, minute_interval):
    forecast_dict = {}
    parking_start = get_parking_start(simulation_day, id_bev)
    parking_end = get_parking_end(simulation_day, id_bev)
    parking_interval_in_minutes_as_list = get_parking_interval_in_minutes_as_list(parking_start, parking_end,
                                                                                  minute_interval)
    for minute in parking_interval_in_minutes_as_list:
        number_of_free_charging_stations = get_number_of_free_charging_stations(minute, charging_power_per_bev,
                                                                                solar_peak_power, simulation_day,
                                                                                minute_interval)
        available_solar_energy_for_bev = get_available_solar_energy_per_minute_for_bev(charging_power_per_bev,
                                                                                       solar_peak_power,
                                                                                       minute, minute_interval)
        forecast_dict[minute] = [number_of_free_charging_stations, available_solar_energy_for_bev]
    return forecast_dict


def get_available_solar_energy_per_minute_for_bev(charging_power_pro_bev, solar_peak_power, minute, minute_interval):
    available_solar_power = get_available_solar_power(solar_peak_power, minute)
    number_of_charging_stations = get_number_of_charging_stations(minute, charging_power_pro_bev, solar_peak_power)
    charging_power_per_bev = get_charging_power_per_bev(available_solar_power, number_of_charging_stations)
    return charging_power_per_bev * (minute_interval / 60)


def get_possible_charging_intervals_list(forecast_dict):
    possible_charging_intervals_list = []
    possible_charging_interval_list = []
    #print(forecast_dict, "Forecast-dict")
    for minute in forecast_dict.keys():
        if forecast_dict[minute][0] >= 1:
            if check_if_in_simulation_time_interval(minute):
                possible_charging_interval_list.append(minute)
        else:
            possible_charging_intervals_list.append(possible_charging_interval_list)
            possible_charging_interval_list = []
    possible_charging_intervals_list.append(possible_charging_interval_list)
    #print(possible_charging_intervals_list, "Possible charging intervals list")
    return possible_charging_intervals_list


def check_if_in_simulation_time_interval(minute):
    if minute < 480 or minute > 960:
        return False
    return True


def get_longest_charging_interval(possible_charging_intervals_list):
    return max(charging_interval_list for charging_interval_list in possible_charging_intervals_list)


def get_charging_energies_dict(forecast_dict, possible_charging_intervals_list):
    charging_energies_dict = {}
    index = 0
    for possible_charging_interval in possible_charging_intervals_list:
        forecast_in_possible_charging_interval_dict = OrderedDict(
            sorted(get_forecast_in_possible_charging_interval_dict(forecast_dict, possible_charging_interval).items()))
        charging_energy_in_interval = 0
        for minute in forecast_in_possible_charging_interval_dict.keys():
            charging_energy_in_interval += forecast_in_possible_charging_interval_dict[minute][1]
        charging_energies_dict[index] = charging_energy_in_interval
        index += 1
    return charging_energies_dict


def shorten_charging_interval_till_fit_fair_share(charging_interval_as_list, forecast_dict, fair_share):
    forecast_in_charging_interval_dict = OrderedDict(sorted(get_forecast_in_possible_charging_interval_dict(
        forecast_dict, charging_interval_as_list).items()))
    charging_energy_in_interval = 0
    for minute in forecast_in_charging_interval_dict.keys():
        charging_energy_in_interval += forecast_in_charging_interval_dict[minute][1]
        if charging_energy_in_interval > fair_share:
            shortened_interval = [x for x in charging_interval_as_list if x < minute]
            if len(shortened_interval) == 1:
                shortened_interval.append(charging_interval_as_list[1])
            return shortened_interval


def get_charging_interval_with_highest_charging_energy(charging_energies_dict, possible_charging_intervals_list):
    #print(charging_energies_dict, "Charging Energies dict")
    index_max_charging_energy = max(charging_energies_dict, key=charging_energies_dict.get)
    #print(index_max_charging_energy, "index_max_charging_energy")
    return possible_charging_intervals_list[index_max_charging_energy]


def get_highest_charging_energy(charging_energies_dict):
    return max(charging_energies_dict.values())


def get_forecast_in_possible_charging_interval_dict(forecast_dict, possible_charging_interval):
    return {key: forecast_dict[key] for key in
            forecast_dict.keys() & possible_charging_interval}


def get_number_of_charging_stations(minute, charging_power_per_bev, solar_peak_power):
    available_solar_power = get_available_solar_power(solar_peak_power, minute)
    return calculate_number_of_charging_stations(available_solar_power, charging_power_per_bev)


def get_number_of_charging_stations_already_allocated(simulation_day, minute, minute_interval):
    number_of_charging_stations_already_allocated = 0
    for id_bev in simulation_day.bevs_dict.get_bevs_dict():
        charging_start = simulation_day.bevs_dict.get_charging_start(id_bev)
        charging_time = simulation_day.bevs_dict.get_charging_time(id_bev)
        if charging_start is not None and charging_time is not None:
            charging_end = calculate_charging_end(charging_start, charging_time)
            charging_interval_in_minutes_as_list = np.arange(charging_start, charging_end, minute_interval)
            if minute in charging_interval_in_minutes_as_list:
                number_of_charging_stations_already_allocated += 1
    return number_of_charging_stations_already_allocated


def get_number_of_free_charging_stations(minute, charging_power_pro_bev, solar_peak_power, simulation_day,
                                         minute_interval):
    number_of_charging_stations = get_number_of_charging_stations(minute, charging_power_pro_bev, solar_peak_power)
    # print(minute, "Minute")
    # print(number_of_charging_stations, "Anzahl an Ladestationen")
    number_of_charging_stations_already_allocated = get_number_of_charging_stations_already_allocated(simulation_day,
                                                                                                      minute,
                                                                                                      minute_interval)
    # print(number_of_charging_stations_already_allocated, "Bereits belegte Ladestationen")
    return number_of_charging_stations - number_of_charging_stations_already_allocated
