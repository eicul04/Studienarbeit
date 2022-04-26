import numpy as np
from simulateDay import simulate_day
from simulationService import calculate_parking_end

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
    set_initial_charging_times(simulation_data, simulation_day, maximum_charging_time, charging_power_per_bev)
    # TODO hier geht dann der Algo richtig los, nachdem die charging List initialisiert wurde
    # update charging_times bei Veränderungen zum ursprünglichen Plan (bevs_dict Parkzeiten)
    # update immer für wartende und noch nicht parkende autos


def init_simulation_data(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data):
    simulate_day(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data)


def set_initial_charging_times(simulation_data, simulation_day, maximum_charging_time, charging_power_per_bev):
    for id_bev in simulation_day.bevs_dict.get_bevs_dict().keys():
        available_solar_power_per_bev_in_parking_interval_dict = get_available_solar_power_in_parking_interval_dict(
            simulation_day, id_bev, simulation_data)
        minute_when_max_available_solar_power_per_bev = get_minute_when_max_available_solar_power_per_bev(
            available_solar_power_per_bev_in_parking_interval_dict)
        charging_start = get_charging_start(minute_when_max_available_solar_power_per_bev, maximum_charging_time)
        charging_end = get_charging_end(minute_when_max_available_solar_power_per_bev, maximum_charging_time)
        set_charging_data(id_bev, simulation_day, charging_start, charging_end)
        reduce_available_solar_power_because_of_charging_slot(charging_power_per_bev,
                                                              get_minute_when_max_available_solar_power_per_bev(
                                                                  available_solar_power_per_bev_in_parking_interval_dict),
                                                              simulation_data)
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
    parking_interval_in_minutes_as_list = np.arange(in_minutes(parking_start), in_minutes(parking_end), 1)
    return {key: simulation_data.available_solar_power_per_bev_per_minute_dict[key] for key in
            simulation_data.available_solar_power_per_bev_per_minute_dict.keys() & parking_interval_in_minutes_as_list}


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


def set_charging_data(id_bev, simulation_day, charging_start, charging_end):
    simulation_day.bevs_dict.add_charging_data_for_forecast(id_bev, charging_start, charging_end)


def reduce_available_solar_power_because_of_charging_slot(charging_power_per_bev, max_minute, simulation_data):
    simulation_data.available_solar_power_per_bev_per_minute_dict[max_minute] -= charging_power_per_bev
