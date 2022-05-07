
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


def update_fueled_solar_energy(available_solar_power_last_interval, simulation_day, minute_interval, minute,
                               simulation_data, charging_bevs_last_interval, bevs_with_charging_end_in_last_interval):
    print("FUEL Charging BEVs last interval: ", charging_bevs_last_interval)
    if len(charging_bevs_last_interval) != 0:

        for id_bev in charging_bevs_last_interval:
            charging_time = get_charging_time_of_last_interval(minute, minute_interval, id_bev, simulation_day,
                                                               bevs_with_charging_end_in_last_interval)
            add_charging_energy_for_charging_interval(charging_bevs_last_interval, id_bev, simulation_day,
                                                      available_solar_power_last_interval, charging_time)


# TODO wenn es ein charging energy downgrade während dem Intervall gibt, muss das Stufenweise in Diagramm
# da interpoliert fehlerhafte solar energy Berechnung okay???
def add_charging_energy_for_charging_interval(charging_bevs_last_interval, id_bev,
                                              simulation_day, available_solar_power_last_interval, charging_time):
    number_of_bevs_total_in_interval = len(charging_bevs_last_interval)
    charging_power_per_bev = get_charging_power_per_bev(available_solar_power_last_interval,
                                                        number_of_bevs_total_in_interval)
    new_charging_energy = calculate_new_charging_energy(charging_power_per_bev, charging_time)
    simulation_day.bevs_dict.add_fueled_charging_energy(id_bev, new_charging_energy)


def get_charging_time_of_last_interval(minute, minute_interval, id_bev, simulation_day,
                                       bevs_with_charging_end_in_last_interval):
    last_minute = minute - minute_interval
    charging_start = get_charging_start_of_last_interval(minute, minute_interval, id_bev, simulation_day)
    charging_end = get_charging_end_of_last_interval(minute, id_bev, simulation_day,
                                                     bevs_with_charging_end_in_last_interval)
    if check_if_charging_start_between_last_interval_and_now(last_minute, charging_start, minute) and \
            check_if_charging_end_between_last_interval_and_now(id_bev, bevs_with_charging_end_in_last_interval):
        return charging_end - charging_start
    if check_if_charging_start_between_last_interval_and_now(last_minute, charging_start, minute) and \
            check_if_charging_end_between_last_interval_and_now(id_bev,
                                                                bevs_with_charging_end_in_last_interval) is False:
        return minute - charging_start
    if check_if_charging_start_between_last_interval_and_now(last_minute, charging_start, minute) is False and \
            check_if_charging_end_between_last_interval_and_now(id_bev, bevs_with_charging_end_in_last_interval):
        return charging_end - last_minute
    return minute_interval


def get_charging_start_of_last_interval(minute, minute_interval, id_bev, simulation_day):
    last_minute = minute - minute_interval
    charging_start = simulation_day.bevs_dict.get_charging_start(id_bev)
    if check_if_charging_start_between_last_interval_and_now(last_minute, charging_start, minute):
        return charging_start
    if check_if_charging_start_between_last_interval_and_now(last_minute, charging_start, minute) is False:
        return last_minute


def get_charging_end_of_last_interval(minute, id_bev, simulation_day,
                                      bevs_with_charging_end_in_last_interval):
    charging_end = simulation_day.bevs_dict.get_charging_end(id_bev)
    print("check_if_charging_end_between_last_interval_and_now: ",
          check_if_charging_end_between_last_interval_and_now(id_bev, bevs_with_charging_end_in_last_interval))
    if check_if_charging_end_between_last_interval_and_now(id_bev, bevs_with_charging_end_in_last_interval):
        return charging_end
    if check_if_charging_end_between_last_interval_and_now(id_bev, bevs_with_charging_end_in_last_interval) is False:
        return minute


def check_if_charging_start_or_end_between_last_interval_and_now(last_minute, charging_start, id_bev,
                                                                 bevs_with_charging_end_in_last_interval, minute):
    if check_if_charging_start_between_last_interval_and_now(last_minute, charging_start, minute) or \
            check_if_charging_end_between_last_interval_and_now(id_bev, bevs_with_charging_end_in_last_interval):
        return True
    return False


def check_if_charging_start_between_last_interval_and_now(last_minute, charging_start, minute):
    if last_minute < charging_start < minute:
        return True
    return False


def check_if_charging_end_between_last_interval_and_now(id_bev, bevs_with_charging_end_in_last_interval):
    if id_bev in bevs_with_charging_end_in_last_interval:
        return True
    return False


def update_charging_time(minute, simulation_day):
    for id_bev in simulation_day.charging_bevs_list.get_charging_bevs_list():
        charging_time = get_charging_time_for_bev_in_charging_list(simulation_day, minute, id_bev)
        simulation_day.bevs_dict.set_charging_time(id_bev, charging_time)


def check_if_solar_power_per_bev_for_next_interval_is_not_null(solar_power_per_bev_for_next_interval):
    if solar_power_per_bev_for_next_interval != 0:
        return True
    return False


def check_if_charging_energy_less_than_next_interval(solar_power_per_bev_for_next_interval, minute_interval,
                                                     residual_charging_energy, id_bev):
    solar_energy_per_bev_for_next_interval = solar_power_per_bev_for_next_interval * (minute_interval / 60)
    if 0 <= residual_charging_energy < solar_energy_per_bev_for_next_interval:
        return True
    return False


def check_if_bev_on_waiting_list(chosen_bev_to_start_charging):
    if chosen_bev_to_start_charging is not None:
        return True
    return False


def check_if_bev_on_charging_list(simulation_day):
    number_of_charging_bevs = simulation_day.charging_bevs_list.get_number_of_charging_bevs()
    if number_of_charging_bevs != 0:
        return True
    return False


def stop_charging(id_bev, simulation_day):
    simulation_day.stop_charging(id_bev)


def stop_parking(id_bev, simulation_day):
    simulation_day.stop_parking(id_bev)


def get_residual_charging_time(residual_charging_energy, solar_power_per_bev_for_next_interval):
    return (residual_charging_energy / solar_power_per_bev_for_next_interval) * 60


def get_residual_charging_energy(already_fueled_charging_energy, fair_share_charging_energy):
    return fair_share_charging_energy - already_fueled_charging_energy


def get_charging_time_for_bev_in_charging_list(simulation_day, minute, id_bev):
    charging_start = simulation_day.bevs_dict.get_charging_start(id_bev)
    if charging_start is not None:
        return calculate_charging_time(minute, charging_start)


def safe_unused_solar_energy(unused_solar_energy, simulation_data):
    simulation_data.add_unused_solar_energy(unused_solar_energy)
