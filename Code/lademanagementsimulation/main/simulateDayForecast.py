from simulateDay import safe_simulation_day_state, update_bevs_in_waiting_bevs_list
from simulationClasses import ParkingState
from simulationData import safe_bev_dict_per_minute, safe_waiting_list_per_minute, \
    safe_available_solar_power_per_bev_per_minute
from simulationService import calculate_parking_end
from timeTransformation import in_minutes


def update_waiting_bevs_forecast(minute, simulation_day, simulation_data, available_solar_power):
    for id_bev in simulation_day.bevs_dict.get_keys():
        if simulation_day.bevs_dict.get_parking_start_in_minutes(id_bev) == minute:
            if check_if_arriving_bev_is_from_optimization_plan(id_bev, simulation_day):
                # don't add to waiting list
                simulation_day.bevs_dict.set_parking_state(id_bev, ParkingState.WAITING)
            simulation_day.add_arriving_waiting_bev(id_bev)
    update_because_parking_time_over(minute, simulation_day)
    safe_simulation_day_state(minute, simulation_day, simulation_data, available_solar_power)


def check_if_arriving_bev_is_from_optimization_plan(id_bev, simulation_day):
    charging_data = simulation_day.bevs_dict.get_charging_data(id_bev)
    if len(charging_data) > 0:
        return True
    return False


def update_because_parking_time_over(current_minute, simulation_day):
    update_bevs_in_waiting_bevs_list(current_minute, simulation_day.waiting_bevs_list,
                                     simulation_day)
    update_bevs_in_charging_bevs_list_if_parking_end_in_minute(current_minute, simulation_day.charging_bevs_list,
                                                               simulation_day)


def update_bevs_in_charging_bevs_list_if_parking_end_in_minute(current_minute, charging_bevs_list, simulation_day):
    for id_bev in charging_bevs_list.get_charging_bevs_list():
        parking_end = calculate_parking_end(simulation_day.bevs_dict.get_parking_start(id_bev),
                                            simulation_day.bevs_dict.get_parking_time(id_bev))
        if in_minutes(parking_end) == current_minute:
            print("stop parking at interval_minute for ", id_bev)
            simulation_day.stop_parking(id_bev)
    simulation_day.remove_from_list(charging_bevs_list)




