import copy

import numpy as np

from data import get_available_solar_power
from simulateDay import simulate_day
from simulationService import calculate_parking_end, calculate_number_of_charging_stations, calculate_charging_end

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
                    bev_data, table_dict, charging_power_per_bev):
    day_in_minute_steps = list(np.around(np.arange(480, 960 + 1, 1), 1))
    for minute in day_in_minute_steps:
        init_simulation_data(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data)
    determine_charging_distribution(charging_power_per_bev, maximum_charging_time, simulation_data, simulation_day,
                                    solar_peak_power)
    # TODO hier geht dann der Algo richtig los, nachdem die charging List initialisiert wurde
    # update charging_times bei Veränderungen zum ursprünglichen Plan (bevs_dict Parkzeiten)
    # update immer für wartende und noch nicht parkende autos


def determine_charging_distribution(charging_power_per_bev, maximum_charging_time, simulation_data, simulation_day,
                                    solar_peak_power):
    for id_bev in simulation_day.bevs_dict.get_bevs_dict().keys():
        available_solar_power_per_bev_in_parking_interval_dict = get_available_solar_power_in_parking_interval_dict(
            simulation_day, id_bev, simulation_data)
        fair_share = calculate_fair_share(available_solar_power_per_bev_in_parking_interval_dict)
        print(fair_share, "Fairer Anteil für BEV")
        set_initial_charging_times(simulation_day, maximum_charging_time, charging_power_per_bev, solar_peak_power,
                                   available_solar_power_per_bev_in_parking_interval_dict, id_bev)
        reduce_available_solar_power_because_of_charging_slot(charging_power_per_bev,
                                                              get_minute_when_max_available_solar_power_per_bev(
                                                                  available_solar_power_per_bev_in_parking_interval_dict),
                                                              simulation_data)


def init_simulation_data(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data):
    simulate_day(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data)


def set_initial_charging_times(simulation_day, maximum_charging_time, charging_power_per_bev, solar_peak_power,
                               available_solar_power_per_bev_in_parking_interval_dict, id_bev):
    minute_when_max_available_solar_power_per_bev = get_minute_when_max_available_solar_power_per_bev(
        available_solar_power_per_bev_in_parking_interval_dict)
    # Wie lange muss BEV um Maximum herum tanken, um fairen Anteil zu erhalten?
    get_necessary_charging_period(id_bev, charging_power_per_bev, solar_peak_power, simulation_day)
    charging_start = get_charging_start(minute_when_max_available_solar_power_per_bev, maximum_charging_time)
    charging_end = get_charging_end(minute_when_max_available_solar_power_per_bev, maximum_charging_time)
    set_charging_data(id_bev, simulation_day, charging_start, charging_end)
    print(simulation_day.bevs_dict.get_bevs_dict())


def get_parking_start(simulation_day, id_bev):
    return simulation_day.bevs_dict.get_parking_start(id_bev)


def get_parking_time(simulation_day, id_bev):
    return simulation_day.bevs_dict.get_parking_time(id_bev)


def get_parking_end(simulation_day, id_bev):
    return calculate_parking_end(get_parking_start(simulation_day, id_bev),
                                 get_parking_time(simulation_day, id_bev))


def get_available_solar_power_in_parking_interval_dict(simulation_day, id_bev, simulation_data):
    parking_start = get_parking_start(simulation_day, id_bev)
    parking_end = get_parking_end(simulation_day, id_bev)
    parking_interval_in_minutes_as_list = get_parking_interval_in_minutes_as_list(parking_start, parking_end)
    return {key: simulation_data.available_solar_power_per_bev_per_minute_dict[key] for key in
            simulation_data.available_solar_power_per_bev_per_minute_dict.keys() & parking_interval_in_minutes_as_list}


def get_parking_interval_in_minutes_as_list(parking_start, parking_end):
    return np.arange(in_minutes(parking_start), in_minutes(parking_end), 1)


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


def check_if_charging_interval_full(available_solar_power, charging_power_pro_bev, number_of_planned_bevs):
    number_of_charging_stations = calculate_number_of_charging_stations(available_solar_power, charging_power_pro_bev)
    if number_of_planned_bevs >= number_of_charging_stations:
        return True
    return False


# TODO check for whole intervall for each minute if parking intervall already full


def reduce_available_solar_power_because_of_charging_slot(charging_power_per_bev, max_minute, simulation_data):
    simulation_data.available_solar_power_per_bev_per_minute_dict[max_minute] -= charging_power_per_bev
    print(simulation_data.available_solar_power_per_bev_per_minute_dict)


# TODO Methode fertig schreiben :)
def get_necessary_charging_period(id_bev, charging_power_pro_bev,
                                  solar_peak_power, simulation_day):
    get_possible_charging_interval(id_bev, charging_power_pro_bev,
                                   solar_peak_power, simulation_day)


def get_possible_charging_interval(id_bev, charging_power_per_bev,
                                   solar_peak_power, simulation_day):
    parking_start = get_parking_start(simulation_day, id_bev)
    parking_end = get_parking_end(simulation_day, id_bev)
    start_of_possible_charging_interval = copy.deepcopy(parking_start)
    # TODO bessere Idee als drunter: dict erstellen (siehe Zettel :D)
    # TODO nach Iteration start_of_possible_charging_interval += 1 & parking_interval_in_minutes_as_list neu berechnen
    parking_interval_in_minutes_as_list = get_parking_interval_in_minutes_as_list(start_of_possible_charging_interval,
                                                                                  parking_end)
    possible_charging_interval = [start_of_possible_charging_interval]
    for minute in parking_interval_in_minutes_as_list:
        number_of_free_charging_stations = get_number_of_free_charging_stations(minute, charging_power_per_bev,
                                                                                solar_peak_power, simulation_day)
        if number_of_free_charging_stations >= 1:
            possible_charging_interval.append(minute)


def calculate_fair_share(available_solar_power_per_bev_in_parking_interval_dict):
    fair_share = 0
    for minute in available_solar_power_per_bev_in_parking_interval_dict.keys():
        fair_share += available_solar_power_per_bev_in_parking_interval_dict[minute] * (1 / 60)
    return fair_share


def get_number_of_charging_stations(minute, charging_power_per_bev, solar_peak_power):
    available_solar_power = get_available_solar_power(solar_peak_power, minute)
    return calculate_number_of_charging_stations(available_solar_power, charging_power_per_bev)


def get_number_of_charging_stations_already_allocated(simulation_day, minute):
    current_bevs_dict = simulation_day.bevs_dict.get_bevs_dict()
    number_of_charging_stations_already_allocated = 0
    for id_bev in current_bevs_dict:
        charging_start = current_bevs_dict.get_charging_start(id_bev)
        charging_time = current_bevs_dict.get_charging_time(id_bev)
        charging_end = calculate_charging_end(charging_start, charging_time)
        charging_interval_in_minutes_as_list = np.arange(charging_start, charging_end, 1)
        if minute in charging_interval_in_minutes_as_list:
            number_of_charging_stations_already_allocated += 1
    return number_of_charging_stations_already_allocated


def get_number_of_free_charging_stations(minute, charging_power_pro_bev, solar_peak_power, simulation_day):
    number_of_charging_stations = get_number_of_charging_stations(minute, charging_power_pro_bev, solar_peak_power)
    number_of_charging_stations_already_allocated = get_number_of_charging_stations_already_allocated(simulation_day,
                                                                                                      minute)
    return number_of_charging_stations - number_of_charging_stations_already_allocated
