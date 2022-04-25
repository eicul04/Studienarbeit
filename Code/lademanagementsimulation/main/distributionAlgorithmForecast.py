import numpy as np

from simulationManagementCalculation import calculate_parking_end


# für ankommendes BEV Prognose berechnen
# für alle anderen BEVs (außer für aufgeladene BEVs) Prognose anpassen
# Störfunktion: Abweichung zum prognostizierten Tagesverlauf der BEVs erzielen

# keine maximale Ladezeit -> Ladezeit wird über Prognose berechnet
# zuerst zur Vereinfachung: ich weiß wann BEVs parken und ich weiß wann wie viel verfügbarer Solarstrom
# ich teile den BEVs die Ladeintervalle so zu, das alle möglichst gleich viel Solarstrom am Ende getankt haben
# aus den Ladeintervallen erstelle ich dann eine Ladeliste

# SimulationData = SimulationDataPrognose
# SimulationDataReal = SimulationDataPrognose + Störfunktion

# TODO Ladeintervalle berechnen
# bev_dict.set_charging_time()
from timeTransformation import in_minutes


def start_algorithm(simulation_data, bev_parking_management):
    init_simulation_data()
    set_charging_times(simulation_data, bev_parking_management)
    # simulate_day() mit Anpassung, dass charging time aus bev dict gelesen wird


def init_simulation_data():
    return "placeholder"
    # im Prinzip simulate_day() aus pollingAlgorithm ausführen


def set_charging_times(simulation_data, bev_parking_management):
    for waiting_list in simulation_data.get_waiting_list_per_minute_dict().values():
        for id_bev in waiting_list:
            parking_start = get_parking_start(bev_parking_management, id_bev)
            parking_end = get_parking_end(bev_parking_management, id_bev)
            available_solar_power_per_bev_per_minute_dict = get_available_solar_power_per_bev_per_minute_dict(
                simulation_data)
            available_solar_power_in_parking_interval_dict = get_available_solar_power_in_parking_interval_dict(
                parking_start, parking_end,
                available_solar_power_per_bev_per_minute_dict)
            determine_charging_interval(id_bev, available_solar_power_in_parking_interval_dict)


def get_parking_start(bev_parking_management, id_bev):
    return bev_parking_management.bevs_dict.get_parking_start(id_bev)


def get_parking_time(bev_parking_management, id_bev):
    return bev_parking_management.bevs_dict.get_parking_time(id_bev)


def get_parking_end(bev_parking_management, id_bev):
    return calculate_parking_end(get_parking_start(bev_parking_management, id_bev),
                                 get_parking_time(bev_parking_management, id_bev))


def get_available_solar_power_per_bev_per_minute_dict(simulation_data):
    return simulation_data.available_solar_power_per_bev_per_minute_dict


def get_available_solar_power_in_parking_interval_dict(parking_start, parking_end,
                                                       available_solar_power_per_bev_per_minute_dict):
    parking_interval_in_minutes_as_list = np.arange(in_minutes(parking_start), in_minutes(parking_end), 1)
    print(parking_interval_in_minutes_as_list, 'Park Intervall in Minuten Liste')
    return {key: available_solar_power_per_bev_per_minute_dict[key] for key in
            available_solar_power_per_bev_per_minute_dict.keys() & parking_interval_in_minutes_as_list}


def determine_charging_interval(id_bev, available_solar_power_in_parking_interval_dict):
    print(available_solar_power_in_parking_interval_dict, 'Verfügbare Solarleistung im Park Intervall pro Minute')
    # schaue: Wann ist available_solar_power_per_bev maximal, in dem Zeitraum wo mein BEV da ist?
    # in diesem Zeitraum lade mein BEV mit ladeleistung_pro_bev
    # bev_dict.set_charging_time()
