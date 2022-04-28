import copy


def calculate_unused_solar_energy(available_solar_power, minute_interval):
    return available_solar_power * (minute_interval / 60)


# Returns Solarenergie in kWh (Ladeleistung * 1/60h)
# -> Ladeleistung ändert sich ggf. pro Minute, deshalb Solarenergie alle Minute berechnen
# und auf bisherige aufaddieren
def calculate_new_fueled_solar_energy(charging_power, solar_energy_fueled_so_far, minute_interval):
    new_solar_energy = charging_power * (minute_interval / 60)
    return solar_energy_fueled_so_far + new_solar_energy


def calculate_parking_end(parking_start, parking_time):
    return parking_start + parking_time


def calculate_charging_end(charging_start, charging_time):
    return charging_start + charging_time


def calculate_charging_time(current_minute, charging_start):
    return current_minute - charging_start


def calculate_number_of_charging_stations(available_solar_power, charging_power_pro_bev):
    if available_solar_power <= 0:
        return 0
    if available_solar_power <= charging_power_pro_bev:
        return 1
    if available_solar_power % charging_power_pro_bev == 0:
        return int(available_solar_power / charging_power_pro_bev)
    remaining_charging_capacity = available_solar_power % charging_power_pro_bev
    # + 1 weil sonst würden BEVs mit mehr als charging_power_pro_bev tanken
    return int((available_solar_power - remaining_charging_capacity) / charging_power_pro_bev) + 1


def get_charging_power_per_bev(available_solar_power, number_of_charging_bevs):
    if number_of_charging_bevs != 0:
        return available_solar_power / number_of_charging_bevs
    return 0


def calculate_number_of_free_charging_stations(number_of_virtual_charging_stations, number_of_charging_bevs):
    return number_of_virtual_charging_stations - number_of_charging_bevs


def calculate_number_of_new_bevs_charging(number_of_virtual_charging_stations, number_of_charging_bevs, minute,
                                          available_solar_power, simulation_day, simulation_data, minute_interval):
    number_of_free_virtual_charging_stations = calculate_number_of_free_charging_stations(
        number_of_virtual_charging_stations, number_of_charging_bevs)
    if simulation_day.waiting_bevs_list.get_number_of_waiting_bevs() == 0:
        safe_unused_solar_energy(available_solar_power, simulation_data, minute_interval)
        print("Solarleistung wird in Leitung eingespeist")
        return 0
    elif simulation_day.waiting_bevs_list.get_number_of_waiting_bevs() < number_of_free_virtual_charging_stations:
        return simulation_day.waiting_bevs_list.get_number_of_waiting_bevs()
    return number_of_free_virtual_charging_stations


def calculate_overflow_of_bevs_charging(number_of_virtual_charging_stations, number_of_charging_bevs):
    return number_of_charging_bevs - number_of_virtual_charging_stations


def update_fueled_solar_energy(charging_power_per_bev, simulation_day, minute_interval):
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        simulation_day.bevs_dict.set_fueled_solar_energy(id_bev, charging_power_per_bev, minute_interval)


def update_charging_time(minute, simulation_day):
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        charging_time = calculate_charging_time(minute, simulation_day.bevs_dict.get_charging_start(id_bev))
        simulation_day.bevs_dict.set_charging_time(id_bev, charging_time)


def safe_unused_solar_energy(available_solar_power, simulation_data, minute_interval):
    simulation_data.add_unused_solar_energy(copy.deepcopy(available_solar_power), minute_interval)
