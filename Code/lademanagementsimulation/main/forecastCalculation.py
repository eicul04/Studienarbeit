import numpy as np

from simulationService import calculate_parking_end
from timeTransformation import in_minutes


def calculate_fair_share_charging_energy(available_solar_power_per_bev_in_parking_interval_dict, minute_interval):
    fair_share = 0
    for minute in available_solar_power_per_bev_in_parking_interval_dict.keys():
        fair_share += available_solar_power_per_bev_in_parking_interval_dict[minute] * (minute_interval / 60)
    return fair_share


def get_parking_start(simulation_day, id_bev):
    return in_minutes(simulation_day.bevs_dict.get_parking_start(id_bev))


def get_parking_time(simulation_day, id_bev):
    return in_minutes(simulation_day.bevs_dict.get_parking_time(id_bev))


def get_parking_end(simulation_day, id_bev):
    return calculate_parking_end(get_parking_start(simulation_day, id_bev),
                                 get_parking_time(simulation_day, id_bev))


def get_available_solar_power_in_parking_interval_dict(simulation_day, id_bev, simulation_data, minute_interval):
    parking_start = adapt_parking_start_to_simulation_start(get_parking_start(simulation_day, id_bev))
    parking_end = adapt_parking_end_to_simulation_end(get_parking_end(simulation_day, id_bev))
    parking_interval_in_minutes_as_list = get_parking_interval_in_minutes_as_list(parking_start, parking_end,
                                                                                  minute_interval)
    return {key: simulation_data.available_solar_power_per_bev_per_minute_dict[key] for key in
            simulation_data.available_solar_power_per_bev_per_minute_dict.keys() &
            parking_interval_in_minutes_as_list}


def adapt_parking_start_to_simulation_start(parking_start):
    if parking_start < 480:
        return 480
    return parking_start


def adapt_parking_end_to_simulation_end(parking_end):
    if parking_end > 960:
        return 960
    return parking_end


def get_parking_interval_in_minutes_as_list(parking_start, parking_end, minute_interval):
    return list(np.arange(parking_start, parking_end, minute_interval))
