import timeTransformation
from bevParkingManagementCalculation import calculate_parking_end, calculate_charging_time


def check_if_parking_time_over(current_minute, bev_parking_management):
    check_parking_time_in_waiting_bevs_list(current_minute, bev_parking_management.waiting_bevs_list,
                                            bev_parking_management)
    check_parking_time_in_charging_bevs_list(current_minute, bev_parking_management.charging_bevs_list,
                                             bev_parking_management)


def check_parking_time_in_waiting_bevs_list(current_minute, waiting_bevs_list, bev_parking_management):
    for id_bev in waiting_bevs_list.get_waiting_bevs_list():
        parking_end = calculate_parking_end(bev_parking_management.bevs_dict.get_parking_start(id_bev),
                                            bev_parking_management.bevs_dict.get_parking_time(id_bev))
        if timeTransformation.in_minutes(parking_end) <= current_minute:
            bev_parking_management.stop_parking(id_bev)
    bev_parking_management.remove_from_list(waiting_bevs_list)


def check_parking_time_in_charging_bevs_list(current_minute, charging_bevs_list, bev_parking_management):
    for id_bev in charging_bevs_list.get_charging_bevs_list():
        parking_end = calculate_parking_end(bev_parking_management.bevs_dict.get_parking_start(id_bev),
                                            bev_parking_management.bevs_dict.get_parking_time(id_bev))
        if timeTransformation.in_minutes(parking_end) <= current_minute:
            bev_parking_management.stop_parking(id_bev)
    bev_parking_management.remove_from_list(charging_bevs_list)
