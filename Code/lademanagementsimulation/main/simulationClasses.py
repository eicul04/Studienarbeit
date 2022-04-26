import timeTransformation
from simulationService import calculate_new_fueled_solar_energy
from enum import Enum
import random

import data
import timeTransformation
from collections.abc import Iterable


class ParkingState(Enum):
    NON_PARKING = "nicht parkend"
    WAITING = "wartend"
    CHARGING = "ladend"


class BevDictionary:

    def __init__(self, number_bevs_per_day):
        self.number_bevs_per_day = number_bevs_per_day
        self.bevs_dict = {}
        self.fill_bevs_dict()

    def get_bevs_dict(self):
        return self.bevs_dict

    def fill_bevs_dict(self):
        id_bevs = list(range(self.number_bevs_per_day))
        self.bevs_dict = {x: [(self.generate_parking_start(self.number_bevs_per_day),
                               self.generate_random_parking_time()),
                              ParkingState.NON_PARKING.value, []] for x in id_bevs}

    def generate_parking_start(self, number_bevs_per_day):
        parking_start_times = [[x] * y for x, y in
                               zip(self.get_timestamps(), self.get_list_bevs_per_timestamps(number_bevs_per_day))]
        parking_start_times = list(self.flatten(parking_start_times))
        return random.choice(parking_start_times)

    def generate_random_parking_time(self):
        return round(random.uniform(3.0, 8.0), 1)

    # parking time between 3 and 8 hours
    def get_timestamps(self):
        df_probability_arrival_time_bev = data.get_probability_arrival_time_bevs()
        return list(timeTransformation.transform_to_hours_as_float(df_probability_arrival_time_bev['Uhrzeit']))

    def get_list_bevs_per_timestamps(self, number_bevs_per_day):
        df_probability_arrival_time_bev = data.get_probability_arrival_time_bevs()
        list_bevs_per_timestamps = [int(x * number_bevs_per_day) for x in
                                    df_probability_arrival_time_bev['Wahrscheinlichkeit Anzahl ankommende BEVs']]
        return list_bevs_per_timestamps

    def flatten(self, input_list):
        for item in input_list:
            if isinstance(item, Iterable) and not isinstance(item, str):
                for x in self.flatten(item):
                    yield x
            else:
                yield item

    def set_parking_state(self, id_bev, state):
        bev_data = self.bevs_dict[id_bev]
        bev_data[1] = state.value

    def get_parking_start(self, id_bev):
        return self.get_parking_data(id_bev)[0]

    def get_parking_time(self, id_bev):
        return self.get_parking_data(id_bev)[1]

    def get_parking_data(self, id_bev):
        bev_data = self.bevs_dict[id_bev]
        return bev_data[0]

    def add_charging_data(self, id_bev, current_minute):
        bev_charging_data = self.bevs_dict[id_bev][2]
        bev_charging_data.append((current_minute, 0, 0))

    def get_charging_time(self, id_bev):
        latest_charging_tuple = self.get_latest_charging_tuple(id_bev)
        return latest_charging_tuple[1]

    def get_charging_start(self, id_bev):
        latest_charging_tuple = self.get_latest_charging_tuple(id_bev)
        return latest_charging_tuple[0]

    def get_charging_data(self, id_bev):
        bev_data = self.bevs_dict[id_bev]
        return bev_data[2]

    def get_keys(self):
        return self.bevs_dict.keys()

    def get_latest_charging_tuple(self, id_bev):
        bev_charging_data = self.get_charging_data(id_bev)
        latest_charging = len(bev_charging_data) - 1
        return bev_charging_data[latest_charging]

    def set_charging_time(self, id_bev, charging_time):
        latest_charging_tuple = self.get_latest_charging_tuple(id_bev)
        latest_charging_tuple_as_list = list(latest_charging_tuple)
        latest_charging_tuple_as_list[1] = charging_time
        new_latest_charging_tuple = tuple(latest_charging_tuple_as_list)
        self.get_charging_data(id_bev).remove(latest_charging_tuple)
        self.get_charging_data(id_bev).append(new_latest_charging_tuple)

    def set_fueled_solar_energy(self, id_bev, charging_power):
        latest_charging_tuple = self.get_latest_charging_tuple(id_bev)
        solar_energy_fueled_so_far = latest_charging_tuple[2]
        latest_charging_tuple_as_list = list(latest_charging_tuple)
        latest_charging_tuple_as_list[2] = round(calculate_new_fueled_solar_energy(charging_power,
                                                                                   solar_energy_fueled_so_far), 3)
        new_latest_charging_tuple = tuple(latest_charging_tuple_as_list)
        self.get_charging_data(id_bev).remove(latest_charging_tuple)
        self.get_charging_data(id_bev).append(new_latest_charging_tuple)


class WaitingBevsList:

    def __init__(self):
        self.waiting_bevs_list = []

    def get_waiting_bevs_list(self):
        return self.waiting_bevs_list

    def get_first_waiting_bev_of_list(self):
        return self.waiting_bevs_list[0]

    def add_bev(self, id_bev):
        self.waiting_bevs_list.append(id_bev)

    def remove_bev(self, id_bev):
        self.waiting_bevs_list.remove(id_bev)
        print(self.waiting_bevs_list, id_bev, "Waiting list with Id removed")

    def get_number_of_waiting_bevs(self):
        return len(self.waiting_bevs_list)


class ChargingBevsList:

    def __init__(self):
        self.charging_bevs_list = []

    def get_charging_bevs_list(self):
        return self.charging_bevs_list

    def get_first_charging_bev_of_list(self):
        return self.charging_bevs_list[0]

    def add_bev(self, id_bev):
        self.charging_bevs_list.append(id_bev)

    def remove_bev(self, id_bev):
        self.charging_bevs_list.remove(id_bev)

    def get_number_of_charging_bevs(self):
        return len(self.charging_bevs_list)


class AlreadyChargedBevsList:

    def __init__(self):
        self.already_charged_bevs_list = []

    def get_charging_bevs_list(self):
        return self.already_charged_bevs_list

    def get_first_charging_bev_of_list(self):
        return self.already_charged_bevs_list[0]

    def add_bev(self, id_bev):
        self.already_charged_bevs_list.append(id_bev)

    def remove_bev(self, id_bev):
        self.already_charged_bevs_list.remove(id_bev)

    def get_number_of_charging_bevs(self):
        return len(self.already_charged_bevs_list)


class SimulationDay:

    def __init__(self, number_bevs_per_day):
        self.charging_bevs_list = ChargingBevsList()
        self.waiting_bevs_list = WaitingBevsList()
        self.already_charged_bevs_list = AlreadyChargedBevsList()
        self.bevs_dict = BevDictionary(number_bevs_per_day)
        self.bevs_to_remove = set()

    def start_charging(self, id_bev, current_minute):
        self.charging_bevs_list.add_bev(id_bev)
        self.waiting_bevs_list.remove_bev(id_bev)
        self.bevs_dict.set_parking_state(id_bev, ParkingState.CHARGING)
        self.bevs_dict.add_charging_data(id_bev, current_minute)

    def stop_charging(self, id_bev):
        self.bevs_to_remove.add(id_bev)
        self.bevs_dict.set_parking_state(id_bev, ParkingState.WAITING)

    def leave_parking(self, id_bev):
        self.bevs_dict.set_parking_state(id_bev, ParkingState.NON_PARKING)

    def stop_parking(self, id_bev):
        self.bevs_to_remove.add(id_bev)
        self.leave_parking(id_bev)

    def remove_from_list(self, list_with_bev_to_remove):
        for id_bev in self.bevs_to_remove:
            list_with_bev_to_remove.remove_bev(id_bev)
        self.bevs_to_remove = set()

    def add_arriving_waiting_bevs(self, minute):
        for id_bev in self.bevs_dict.get_keys():
            if timeTransformation.in_minutes(self.bevs_dict.get_parking_start(id_bev)) == minute:
                self.waiting_bevs_list.add_bev(id_bev)
                self.bevs_dict.set_parking_state(id_bev, ParkingState.WAITING)


class ForecastSimulationDay:

    def __init__(self, bevs_dict):
        self.bevs_dict = bevs_dict

    def set_charging_time(self, id_bev, charging_tuple):
        self.bevs_dict[id_bev][2] = charging_tuple
