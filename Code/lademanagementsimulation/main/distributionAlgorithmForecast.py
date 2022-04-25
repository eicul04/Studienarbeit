import numpy as np
import copy

from simulationClasses import ForecastSimulationDay
from simulationService import calculate_parking_end


# für ankommendes BEV Prognose berechnen
# für alle anderen BEVs (außer für aufgeladene BEVs) Prognose anpassen
# Störfunktion: Abweichung zum prognostizierten Tagesverlauf der BEVs erzielen
# als Störfunktion einfach neuen SimulationDay?

# keine maximale Ladezeit -> Ladezeit wird über Prognose berechnet
# zuerst zur Vereinfachung: ich weiß wann BEVs parken und ich weiß wann wie viel verfügbarer Solarstrom
# ich teile den BEVs die Ladeintervalle so zu, das alle möglichst gleich viel Solarstrom am Ende getankt haben
# aus den Ladeintervallen erstelle ich dann eine Ladeliste

# SimulationData = SimulationDataPrognose
# SimulationDataReal = SimulationDataPrognose + Störfunktion

# TODO Ladeintervalle berechnen
# bev_dict.set_charging_time()
from timeTransformation import in_minutes


def start_algorithm(simulation_data, simulation_day, maximum_charging_time):
    init_simulation_data()
    set_charging_times(simulation_data, simulation_day, maximum_charging_time)
    # simulate_day() mit Anpassung, dass charging time aus bev dict gelesen wird


def init_simulation_data():
    return "placeholder"
    # im Prinzip simulate_day() aus pollingAlgorithm ausführen


def set_charging_times(simulation_data, simulation_day, maximum_charging_time):
    for waiting_list in simulation_data.get_waiting_list_per_minute_dict().values():
        for id_bev in waiting_list:
            available_solar_power_per_bev_in_parking_interval_dict = get_available_solar_power_in_parking_interval_dict(
                simulation_day, id_bev, simulation_data)
            charging_interval = get_charging_interval(available_solar_power_per_bev_in_parking_interval_dict, maximum_charging_time)
            set_charging_interval(id_bev, simulation_day, charging_interval)


def get_parking_start(simulation_day, id_bev):
    return simulation_day.bevs_dict.get_parking_start(id_bev)


def get_parking_time(simulation_day, id_bev):
    return simulation_day.bevs_dict.get_parking_time(id_bev)


def get_parking_end(simulation_day, id_bev):
    return calculate_parking_end(get_parking_start(simulation_day, id_bev),
                                 get_parking_time(simulation_day, id_bev))


def get_available_solar_power_per_bev_per_minute_dict(simulation_data):
    return simulation_data.available_solar_power_per_bev_per_minute_dict


def get_available_solar_power_in_parking_interval_dict(simulation_day, id_bev, simulation_data):
    parking_start = get_parking_start(simulation_day, id_bev)
    parking_end = get_parking_end(simulation_day, id_bev)
    available_solar_power_per_bev_per_minute_dict = get_available_solar_power_per_bev_per_minute_dict(
        simulation_data)
    parking_interval_in_minutes_as_list = np.arange(in_minutes(parking_start), in_minutes(parking_end), 1)
    return {key: available_solar_power_per_bev_per_minute_dict[key] for key in
            available_solar_power_per_bev_per_minute_dict.keys() & parking_interval_in_minutes_as_list}


def get_charging_interval(available_solar_power_per_bev_in_parking_interval_dict, maximum_charging_time):
    max_minute = max(available_solar_power_per_bev_in_parking_interval_dict, key=available_solar_power_per_bev_in_parking_interval_dict.get)
    print(max_minute, "Max Minute")
    max_available_solar_power_per_bev = max(available_solar_power_per_bev_in_parking_interval_dict.values())
    print(max_available_solar_power_per_bev, "Max Verfügbarer Solarstrom pro BEV")
    # max_available_solar_power_per_bev ist Mittelpunkt für Ladezeitraum, sagen wir erstmal alle laden 30 min
    # dann setzten wir Ladestart auf max_available_solar_power_per_bev-15min und Ladeende auf max_available_solar_power_per_bev+15min
    # TODO Abfrage ob Charging Start außerhalb von Ladeintervall ( 8.00 - 16.00 Uhr liegt)
    charging_start = max_minute - (maximum_charging_time / 2)
    charging_end = max_minute + (maximum_charging_time / 2)
    charging_interval = (charging_start, charging_end)
    print(charging_interval, "Ladeintervall")
    return charging_interval


def set_charging_interval(id_bev, simulation_day, charging_tuple):
    # TODO sicher ob eine neue Klasse ForecastSimulationDay, die dann alte BEV Generierung zugewiesen bekommt
    #  bzw. neue BEV Generierung bekommt ???
    #simulation_day.bev_dict.set_charging_time(charging_interval)
    # Remove charging_data, parking_state, ... oder nur ID  und parking_data behalten
    # ForecastSimulationDay {id: (parking_start, parking_end), (charging_start, charging_end)}
    generated_bevs_dict = copy.deepcopy(simulation_day.bevs_dict.get_bevs_dict())
    forecastSimulationDay = ForecastSimulationDay(generated_bevs_dict)
    forecastSimulationDay.set_charging_time(id_bev, charging_tuple)

    # in diesem Zeitraum lade mein BEV mit ladeleistung_pro_bev
    # bev_dict.set_charging_time()
    # available_solar_power reduzieren: available_solar_power_per_bev - ladeleistung_pro_bev
    # und dann von nächstem BEV max bestimmen
