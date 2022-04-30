import copy

from timeTransformation import in_minutes


def calculate_unused_solar_energy(available_solar_power, minute_interval):
    return available_solar_power * (minute_interval / 60)


# Returns Solarenergie in kWh (Ladeleistung * 1/60h)
# -> Ladeleistung ändert sich ggf. pro Minute, deshalb Solarenergie alle Minute berechnen
# und auf bisherige aufaddieren
def calculate_new_charging_energy(charging_power, minute_interval):
    return charging_power * (minute_interval / 60)


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


def calculate_overflow_of_bevs_charging(number_of_virtual_charging_stations, number_of_charging_bevs):
    return number_of_charging_bevs - number_of_virtual_charging_stations


def update_fueled_solar_energy(available_solar_power_last_interval, simulation_day, minute_interval, minute, simulation_data):
    # Number of charging bevs für das letzte Intervall bekommen
    if minute != 480:
        last_interval = minute - minute_interval
        number_of_charging_bevs_of_last_interval = len(simulation_data.charging_list_per_minute_dict[last_interval])
        if number_of_charging_bevs_of_last_interval != 0:
            charging_power_per_bev = get_charging_power_per_bev(available_solar_power_last_interval, number_of_charging_bevs_of_last_interval)
            for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
                charging_time = get_charging_time_for_bev_in_charging_list(simulation_day, minute, id_bev)
                if charging_time % minute_interval == 0:
                    print("Update Charging energy of BEVs which were added in interval")
                    new_charging_energy = calculate_new_charging_energy(charging_power_per_bev, minute_interval)
                    simulation_day.bevs_dict.add_fueled_charging_energy(id_bev, new_charging_energy)
                else:
                    print("Update Charging energy of BEVs which came between intervals")
                    charging_interval = charging_time % minute_interval
                    print("charging interval zur Energie Berechnung: ", charging_interval)
                    new_charging_energy = calculate_new_charging_energy(charging_power_per_bev, charging_interval)
                    simulation_day.bevs_dict.add_fueled_charging_energy(id_bev, new_charging_energy)


def update_charging_time(minute, simulation_day):
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        charging_time = get_charging_time_for_bev_in_charging_list(simulation_day, minute, id_bev)
        simulation_day.bevs_dict.set_charging_time(id_bev, charging_time)


def get_charging_time_for_bev_in_charging_list(simulation_day, minute, id_bev):
    charging_start = simulation_day.bevs_dict.get_charging_start(id_bev)
    if charging_start is not None:
        return calculate_charging_time(minute, charging_start)


def safe_unused_solar_energy(unused_solar_energy, simulation_data):
    simulation_data.add_unused_solar_energy(unused_solar_energy)
