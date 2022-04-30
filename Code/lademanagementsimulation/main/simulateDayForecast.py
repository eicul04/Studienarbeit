from simulateDay import safe_simulation_day_state, update_bevs_in_waiting_bevs_list
from simulationData import safe_bev_dict_per_minute, safe_waiting_list_per_minute, \
    safe_available_solar_power_per_bev_per_minute
from simulationService import calculate_parking_end
from timeTransformation import in_minutes


def simulate_day_forecast(minute, solar_peak_power, simulation_day, bev_data, table_dict, simulation_data):
    update_waiting_bevs_forecast(minute, simulation_day)
    safe_simulation_day_state(minute, simulation_day, bev_data, table_dict, solar_peak_power, simulation_data)


def update_waiting_bevs_forecast(minute, simulation_day):
    simulation_day.add_arriving_waiting_bevs(minute)
    update_because_parking_time_over(minute, simulation_day)


def update_because_parking_time_over(current_minute, simulation_day):
    update_bevs_in_waiting_bevs_list(current_minute, simulation_day.waiting_bevs_list,
                                     simulation_day)
    update_bevs_in_charging_bevs_list_if_parking_end_in_minute(current_minute, simulation_day.charging_bevs_list,
                                                               simulation_day)


def update_bevs_in_charging_bevs_list_if_parking_end_in_minute(current_minute, charging_bevs_list, simulation_day):
    for id_bev in charging_bevs_list.get_charging_bevs_list():
        parking_end = calculate_parking_end(simulation_day.bevs_dict.get_parking_start(id_bev),
                                            simulation_day.bevs_dict.get_parking_time(id_bev))
        print(in_minutes(parking_end), "parking end")
        print(current_minute, "current minute")
        if in_minutes(parking_end) == current_minute:
            print("stop parking at interval_minute for ", id_bev)
            simulation_day.stop_parking(id_bev)
    simulation_day.remove_from_list(charging_bevs_list)




