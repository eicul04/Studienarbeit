from calculation import get_available_solar_power_linear_interpolated
from dataChecks import check_availability_solar_power
from simulationService import update_fueled_solar_energy, calculate_overflow_of_bevs_charging, \
    calculate_number_of_charging_stations, safe_unused_solar_energy, calculate_unused_solar_energy


def check_if_free_charging_stations(number_of_free_charging_stations):
    if number_of_free_charging_stations > 0:
        return True
    return False


def check_if_new_bevs_for_charging(simulation_day):
    number_of_waiting_bevs = simulation_day.waiting_bevs_list.get_number_of_waiting_bevs()
    number_of_charging_bevs = get_number_of_charging_bevs(simulation_day)
    if number_of_waiting_bevs == 0 and number_of_charging_bevs == 0:
        return False
    return True


def get_number_of_charging_stations(available_solar_power, charging_power_pro_bev):
    return calculate_number_of_charging_stations(available_solar_power, charging_power_pro_bev)


def get_number_of_charging_bevs(simulation_day):
    return simulation_day.charging_bevs_list.get_number_of_charging_bevs()


def get_number_of_available_charging_stations(number_of_charging_stations, number_of_charging_bevs,
                                              number_of_planned_bevs_from_post_optimization):
    return number_of_charging_stations - number_of_charging_bevs - number_of_planned_bevs_from_post_optimization


def add_charging_bevs(number_of_bevs_to_add, minute, simulation_day):
    iterator = 0
    while iterator < number_of_bevs_to_add:
        first_bev_waiting_on_list = simulation_day.waiting_bevs_list.get_first_waiting_bev_of_list()
        simulation_day.start_charging(first_bev_waiting_on_list)
        simulation_day.overwrite_charging_data(first_bev_waiting_on_list, minute)
        iterator += 1


def add_charging_bev_from_optimization_plan(id_bev, simulation_day):
    simulation_day.start_charging(id_bev)


def get_number_of_unoccupied_charging_stations(number_of_free_charging_stations, number_of_waiting_bevs):
    if number_of_waiting_bevs > number_of_free_charging_stations:
        return 0
    return number_of_free_charging_stations - number_of_waiting_bevs


# TODO in the middle of interval
def update_unused_solar_energy(solar_peak_power, minute, simulation_data, minute_interval):
    if check_availability_solar_power(solar_peak_power, minute):
        unused_solar_power = get_available_solar_power_linear_interpolated(solar_peak_power, minute + minute_interval/2)
        unused_solar_energy = calculate_unused_solar_energy(unused_solar_power, minute_interval)
        safe_unused_solar_energy(unused_solar_energy, simulation_data)

