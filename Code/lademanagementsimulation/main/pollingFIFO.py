

def add_charging_bevs(number_of_new_bevs_charging, minute, bev_parking_management):
    number_of_new_bevs_charging_as_list = list(range(0, number_of_new_bevs_charging))
    for item in number_of_new_bevs_charging_as_list:
        bev_parking_management.start_charging(bev_parking_management.waiting_bevs_list.get_first_waiting_bev_of_list(), minute)


def stop_charging_bevs(overflow_of_bevs_charging, bev_parking_management):
    overflow_of_bevs_charging_as_list = list(range(0, overflow_of_bevs_charging))
    for item in overflow_of_bevs_charging_as_list:
        bev_parking_management.stop_charging(bev_parking_management.charging_bevs_list.get_first_charging_bev_of_list())