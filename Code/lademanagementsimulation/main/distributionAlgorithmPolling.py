import copy

import bevParkingManagementCalculation
import bevParkingManagementChecks
import numpy as np
import dataChecks
import data
import bevParkingManagementVisualisation

# TODO Visualization: Diagramm Anzahl Waiting und Charging BEVs
# TODO Fairness: weitere Listen: BEVs die schon einmal geladen haben (und noch da sind)


def start_simulation(solar_peak_power, max_charging_time, charging_power_pro_bev,
                     bev_parking_management, visualisation_object, table_dict):
    simulate_day(solar_peak_power, max_charging_time, charging_power_pro_bev, bev_parking_management,
                 visualisation_object, table_dict)


def simulate_day(solar_peak_power, max_charging_time, charging_power_pro_bev, bev_parking_management, visualisation_object, table_dict):
    day_in_minute_steps = list(np.around(np.arange(480, 960 + 1, 1), 1))
    for minute in day_in_minute_steps:
        check_and_update_parking_data(solar_peak_power, minute, max_charging_time,
                                      charging_power_pro_bev, bev_parking_management)
        safe_bev_dict_per_minute(minute, bev_parking_management, visualisation_object, table_dict, solar_peak_power)



def check_and_update_parking_data(solar_peak_power, minute, max_charging_time,
                                  charging_power_pro_bev, bev_parking_management):
    bev_parking_management.update_waiting_bevs(minute)
    update_charging_time(minute, bev_parking_management)
    bevParkingManagementChecks.check_if_charging_time_over(minute, max_charging_time, bev_parking_management)
    bevParkingManagementChecks.check_if_parking_time_over(minute, bev_parking_management)
    if dataChecks.check_availability_solar_power(solar_peak_power, minute):
        available_solar_power = data.get_available_solar_power(solar_peak_power, minute)
        update_charging_data(minute, available_solar_power, charging_power_pro_bev, bev_parking_management)
        update_fueled_solar_energy(available_solar_power, bev_parking_management)


def update_fueled_solar_energy(available_solar_power, bev_parking_management):
    number_of_charging_bevs = bev_parking_management.charging_bevs_list.get_number_of_charging_bevs()
    if number_of_charging_bevs != 0:
        charging_power_per_bev = get_charging_power_per_bev(available_solar_power, number_of_charging_bevs)
        for id_bev in bev_parking_management.charging_bevs_list.get_charging_bevs_list():
            bev_parking_management.bevs_dict.set_fueled_solar_energy(id_bev, charging_power_per_bev)


def update_charging_data(minute, available_solar_power, charging_power_pro_bev, bev_parking_management):
    number_of_virtual_charging_stations = calculate_number_of_virtual_charging_stations(
        available_solar_power,
        charging_power_pro_bev)
    number_of_charging_bevs = bev_parking_management.charging_bevs_list.get_number_of_charging_bevs()
    update_charging_bevs(number_of_virtual_charging_stations, number_of_charging_bevs, minute, available_solar_power, bev_parking_management)


def update_charging_bevs(number_of_virtual_charging_stations, number_of_charging_bevs, minute,
                         available_solar_power, bev_parking_management):
    if number_of_charging_bevs < number_of_virtual_charging_stations:
        add_charging_bevs(calculate_number_of_new_bevs_charging(number_of_virtual_charging_stations,
                                                                number_of_charging_bevs, minute, available_solar_power, bev_parking_management),
                          minute, bev_parking_management)
    elif number_of_charging_bevs > number_of_virtual_charging_stations:
        stop_charging_bevs(calculate_overflow_of_bevs_charging(number_of_virtual_charging_stations,
                                                               number_of_charging_bevs), bev_parking_management)


def update_charging_time(minute, bev_parking_management):
    for id_bev in bev_parking_management.charging_bevs_list.get_charging_bevs_list():
        charging_time = bevParkingManagementCalculation\
            .calculate_charging_time(minute, bev_parking_management.bevs_dict.get_charging_start(id_bev))
        bev_parking_management.bevs_dict.set_charging_time(id_bev, charging_time)


def add_charging_bevs(number_of_new_bevs_charging, minute, bev_parking_management):
    number_of_new_bevs_charging_as_list = list(range(0, number_of_new_bevs_charging))
    for item in number_of_new_bevs_charging_as_list:
        bev_parking_management.start_charging(bev_parking_management.waiting_bevs_list.get_first_waiting_bev_of_list(), minute)


def stop_charging_bevs(overflow_of_bevs_charging, bev_parking_management):
    overflow_of_bevs_charging_as_list = list(range(0, overflow_of_bevs_charging))
    for item in overflow_of_bevs_charging_as_list:
        bev_parking_management.stop_charging(bev_parking_management.charging_bevs_list.get_first_charging_bev_of_list())


def calculate_number_of_virtual_charging_stations(available_solar_power, charging_power_pro_bev):
    if available_solar_power <= charging_power_pro_bev:
        return 1
    if available_solar_power % charging_power_pro_bev == 0:
        return int(available_solar_power / charging_power_pro_bev)
    remaining_charging_capacity = available_solar_power % charging_power_pro_bev
    # + 1 für BEV, das dann die Reste tankt
    return int((available_solar_power - remaining_charging_capacity) / charging_power_pro_bev) + 1


def get_charging_power_per_bev(available_solar_power, number_of_charging_bevs):
    return available_solar_power / number_of_charging_bevs


def calculate_number_of_free_virtual_charging_stations(number_of_virtual_charging_stations, number_of_charging_bevs):
    return number_of_virtual_charging_stations - number_of_charging_bevs


# TODO unit test
def calculate_number_of_new_bevs_charging(number_of_virtual_charging_stations, number_of_charging_bevs, minute, available_solar_power, bev_parking_management):
    number_of_free_virtual_charging_stations = calculate_number_of_free_virtual_charging_stations(
        number_of_virtual_charging_stations, number_of_charging_bevs)
    if bev_parking_management.waiting_bevs_list.get_number_of_waiting_bevs() == 0:
        bev_parking_management.set_unused_solar_energy(available_solar_power)
        print("Solarleistung wird in Leitung eingespeist")
        return 0
    elif bev_parking_management.waiting_bevs_list.get_number_of_waiting_bevs() < number_of_free_virtual_charging_stations:
        return bev_parking_management.waiting_bevs_list.get_number_of_waiting_bevs()
    return number_of_free_virtual_charging_stations


def calculate_overflow_of_bevs_charging(number_of_virtual_charging_stations, number_of_charging_bevs):
    return number_of_charging_bevs - number_of_virtual_charging_stations


def safe_bev_dict_per_minute(minute, bev_parking_management, visualisation_object, table_dict, solar_peak_power):
    current_bevs_dict = copy.deepcopy(bev_parking_management.bevs_dict)
    visualisation_object.add_bev_dict(minute, current_bevs_dict)
    bev_dict_specific_minute = visualisation_object.get_bev_dict(minute)
    current_table = bevParkingManagementVisualisation.create_plotly_table(bev_dict_specific_minute, solar_peak_power, minute)
    table_dict.add_table(minute, current_table)

