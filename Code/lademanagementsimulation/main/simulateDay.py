from simulationData import safe_bev_dict_per_minute, safe_waiting_list_per_minute, \
    safe_available_solar_power_per_bev_per_minute
from simulationService import calculate_parking_end
from timeTransformation import in_minutes


def simulate_day(minute, simulation_day, simulation_data, available_solar_power):
    update_waiting_bevs(minute, simulation_day)
    safe_simulation_day_state(minute, simulation_day, simulation_data, available_solar_power)


def update_waiting_bevs(minute, simulation_day):
    for id_bev in simulation_day.bevs_dict.get_keys():
        if simulation_day.bevs_dict.get_parking_start_in_minutes(id_bev) == minute:
            simulation_day.add_arriving_waiting_bev(id_bev)
    update_because_parking_time_over(minute, simulation_day)


def update_because_parking_time_over(current_minute, simulation_day):
    update_bevs_in_waiting_bevs_list(current_minute, simulation_day.waiting_bevs_list,
                                     simulation_day)
    update_bevs_in_charging_bevs_list(current_minute, simulation_day.charging_bevs_list,
                                      simulation_day)


def update_bevs_in_waiting_bevs_list(current_minute, waiting_bevs_list, simulation_day):
    for id_bev in waiting_bevs_list.get_waiting_bevs_list():
        parking_end = calculate_parking_end(simulation_day.bevs_dict.get_parking_start(id_bev),
                                            simulation_day.bevs_dict.get_parking_time(id_bev))
        if in_minutes(parking_end) <= current_minute:
            simulation_day.stop_parking(id_bev)
    simulation_day.remove_from_list(waiting_bevs_list)


def update_bevs_in_charging_bevs_list(current_minute, charging_bevs_list, simulation_day):
    for id_bev in charging_bevs_list.get_charging_bevs_list():
        parking_end = calculate_parking_end(simulation_day.bevs_dict.get_parking_start(id_bev),
                                            simulation_day.bevs_dict.get_parking_time(id_bev))
        if in_minutes(parking_end) <= current_minute:
            simulation_day.stop_parking(id_bev)
    simulation_day.remove_from_list(charging_bevs_list)


def safe_simulation_day_state(minute, simulation_day, simulation_data, available_solar_power):
    safe_waiting_list_per_minute(simulation_day, simulation_data, minute)
    safe_available_solar_power_per_bev_per_minute(simulation_data, minute, available_solar_power)




