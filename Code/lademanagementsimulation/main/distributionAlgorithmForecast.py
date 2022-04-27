import copy
from collections import OrderedDict

import numpy as np

from data import get_available_solar_power
from simulateDay import simulate_day
from simulationService import calculate_parking_end, calculate_number_of_charging_stations, calculate_charging_end, \
    get_charging_power_per_bev

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

# TODO Ladeintervalle berechnen
# bev_dict.set_charging_time()
from timeTransformation import in_minutes


def start_algorithm(simulation_data, simulation_day, maximum_charging_time, solar_peak_power,
                    bev_data, table_dict, charging_power_per_bev, minute_interval):
    day_in_minute_interval_steps = list(np.around(np.arange(480, 960 + 1, minute_interval), 1))
    for minute in day_in_minute_interval_steps:
        init_simulation_data(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data)
    determine_charging_distribution(charging_power_per_bev, maximum_charging_time, simulation_data, simulation_day,
                                    solar_peak_power, minute_interval)
    # TODO hier geht dann der Algo richtig los, nachdem die charging List initialisiert wurde
    # update charging_times bei Veränderungen zum ursprünglichen Plan (bevs_dict Parkzeiten)
    # update immer für wartende und noch nicht parkende autos


def determine_charging_distribution(charging_power_per_bev, maximum_charging_time, simulation_data, simulation_day,
                                    solar_peak_power, minute_interval):
    print("Start: BEVs_dict", simulation_day.bevs_dict.get_bevs_dict())
    for id_bev in simulation_day.bevs_dict.get_bevs_dict().keys():
        print("Updated BEVs_dict", simulation_day.bevs_dict.get_bevs_dict())
        print("\n")
        print("für BEV mit ID", id_bev)
        available_solar_power_per_bev_in_parking_interval_dict = OrderedDict(sorted(
            get_available_solar_power_in_parking_interval_dict(
                simulation_day, id_bev, simulation_data, minute_interval).items()))
        # print(available_solar_power_per_bev_in_parking_interval_dict, "available_solar_power_per_bev_in_parking_interval_dict")
        fair_share = calculate_fair_share(available_solar_power_per_bev_in_parking_interval_dict)
        print(fair_share, "Fairer Anteil für BEV")
        set_initial_charging_times(simulation_day, maximum_charging_time, charging_power_per_bev, solar_peak_power,
                                   available_solar_power_per_bev_in_parking_interval_dict, id_bev, minute_interval,
                                   fair_share)


def init_simulation_data(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data):
    simulate_day(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data)


# TODO update set_charging_data
def set_initial_charging_times(simulation_day, maximum_charging_time, charging_power_per_bev, solar_peak_power,
                               available_solar_power_per_bev_in_parking_interval_dict, id_bev, minute_interval,
                               fair_share):
    minute_when_max_available_solar_power_per_bev = get_minute_when_max_available_solar_power_per_bev(
        available_solar_power_per_bev_in_parking_interval_dict)
    charging_interval = get_charging_interval(id_bev, charging_power_per_bev, solar_peak_power, simulation_day, minute_interval, fair_share)
    # TODO delete 1. Ansatz um Maximum rumtanken?
    # charging_start = get_charging_start(minute_when_max_available_solar_power_per_bev, maximum_charging_time)
    # charging_end = get_charging_end(minute_when_max_available_solar_power_per_bev, maximum_charging_time)
    set_charging_data(id_bev, simulation_day, charging_interval[0], charging_interval[1])


def get_parking_start(simulation_day, id_bev):
    return simulation_day.bevs_dict.get_parking_start(id_bev)


def get_parking_time(simulation_day, id_bev):
    return simulation_day.bevs_dict.get_parking_time(id_bev)


def get_parking_end(simulation_day, id_bev):
    return calculate_parking_end(get_parking_start(simulation_day, id_bev),
                                 get_parking_time(simulation_day, id_bev))


def get_available_solar_power_in_parking_interval_dict(simulation_day, id_bev, simulation_data, minute_interval):
    parking_start = get_parking_start(simulation_day, id_bev)
    parking_end = get_parking_end(simulation_day, id_bev)
    parking_interval_in_minutes_as_list = get_parking_interval_in_minutes_as_list(parking_start, parking_end,
                                                                                  minute_interval)
    return {key: simulation_data.available_solar_power_per_bev_per_minute_dict[key] for key in
            simulation_data.available_solar_power_per_bev_per_minute_dict.keys() &
            parking_interval_in_minutes_as_list}


def get_parking_interval_in_minutes_as_list(parking_start, parking_end, minute_interval):
    return list(np.arange(in_minutes(parking_start), in_minutes(parking_end), minute_interval))


def get_minute_when_max_available_solar_power_per_bev(available_solar_power_per_bev_in_parking_interval_dict):
    return max(available_solar_power_per_bev_in_parking_interval_dict,
               key=available_solar_power_per_bev_in_parking_interval_dict.get)


def get_max_available_solar_power_per_bev(available_solar_power_per_bev_in_parking_interval_dict):
    return max(available_solar_power_per_bev_in_parking_interval_dict.values())


# TODO Abfrage ob Charging Start außerhalb von Ladeintervall ( 8.00 - 16.00 Uhr liegt)
def get_charging_start(minute_when_max_available_solar_power_per_bev, maximum_charging_time):
    return int(minute_when_max_available_solar_power_per_bev - (maximum_charging_time / 2))


def get_charging_end(minute_when_max_available_solar_power_per_bev, maximum_charging_time):
    return int(minute_when_max_available_solar_power_per_bev + (maximum_charging_time / 2))


# TODO Abfrage, das maximal so viele in charging intervall wie available_charging_stations
def set_charging_data(id_bev, simulation_day, charging_start, charging_end):
    charging_time = charging_end - charging_start
    simulation_day.bevs_dict.add_charging_data_for_forecast(id_bev, charging_start, charging_time)


def get_charging_interval(id_bev, charging_power_per_bev,
                          solar_peak_power, simulation_day, minute_interval, fair_share):
    forecast_dict = get_forecast_dict(id_bev, charging_power_per_bev, solar_peak_power, simulation_day, minute_interval)
    possible_charging_intervals_list = get_possible_charging_intervals_list(forecast_dict)
    if any(possible_charging_intervals_list):
        charging_energies_dict = get_charging_energies_dict(forecast_dict, possible_charging_intervals_list)
        highest_charging_energy = get_highest_charging_energy(charging_energies_dict)
        charging_interval_as_list = get_charging_interval_with_highest_charging_energy(charging_energies_dict,
                                                                                       possible_charging_intervals_list)
        if highest_charging_energy > fair_share:
            shortened_charging_interval_as_list = shorten_charging_interval_till_fit_fair_share(
                charging_interval_as_list, forecast_dict, fair_share)
            return create_charging_interval(shortened_charging_interval_as_list)
        else:
            return create_charging_interval(charging_interval_as_list)
    print("No charging slot available")
    # TODO Was machen wenn kein charging slot frei?


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
                                                                                       minute)
        forecast_dict[minute] = [number_of_free_charging_stations, available_solar_energy_for_bev]
    return forecast_dict


def get_available_solar_energy_per_minute_for_bev(charging_power_pro_bev, solar_peak_power, minute):
    available_solar_power = get_available_solar_power(solar_peak_power, minute)
    number_of_charging_stations = get_number_of_charging_stations(minute, charging_power_pro_bev, solar_peak_power)
    charging_power_per_bev = get_charging_power_per_bev(available_solar_power, number_of_charging_stations)
    return charging_power_per_bev * (1 / 60)


def get_possible_charging_intervals_list(forecast_dict):
    possible_charging_intervals_list = []
    possible_charging_interval_list = []
    print(forecast_dict, "Forecast-dict")
    for minute in forecast_dict.keys():
        if forecast_dict[minute][0] >= 1:
            possible_charging_interval_list.append(minute)
        else:
            possible_charging_intervals_list.append(possible_charging_interval_list)
            possible_charging_interval_list = []
    possible_charging_intervals_list.append(possible_charging_interval_list)
    print(possible_charging_intervals_list, "Possible charging intervals list")
    return possible_charging_intervals_list


def get_longest_charging_interval(possible_charging_intervals_list):
    return max(charging_interval_list for charging_interval_list in possible_charging_intervals_list)


def get_charging_energies_dict(forecast_dict, possible_charging_intervals_list):
    charging_energies_dict = {}
    index = 0
    for possible_charging_interval in possible_charging_intervals_list:
        forecast_in_possible_charging_interval_dict = OrderedDict(sorted(get_forecast_in_possible_charging_interval_dict(forecast_dict, possible_charging_interval).items()))
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
            return shortened_interval


def get_charging_interval_with_highest_charging_energy(charging_energies_dict, possible_charging_intervals_list):
    print(charging_energies_dict, "Charging Energies dict")
    index_max_charging_energy = max(charging_energies_dict, key=charging_energies_dict.get)
    print(index_max_charging_energy, "index_max_charging_energy")
    return possible_charging_intervals_list[index_max_charging_energy]


def get_highest_charging_energy(charging_energies_dict):
    return max(charging_energies_dict.values())


def get_forecast_in_possible_charging_interval_dict(forecast_dict, possible_charging_interval):
    return {key: forecast_dict[key] for key in
            forecast_dict.keys() & possible_charging_interval}


def calculate_fair_share(available_solar_power_per_bev_in_parking_interval_dict):
    fair_share = 0
    for minute in available_solar_power_per_bev_in_parking_interval_dict.keys():
        fair_share += available_solar_power_per_bev_in_parking_interval_dict[minute] * (1 / 60)
    return fair_share


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
