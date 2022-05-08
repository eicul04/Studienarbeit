import copy

import plotly.graph_objects as go

import data
from calculation import calculate_available_solar_power_per_bev, get_available_solar_power_linear_interpolated
from simulationService import calculate_unused_solar_energy
from timeTransformation import as_time_of_day_from_hour, as_time_of_day_from_minute


class SimulationData:

    def __init__(self):
        self.waiting_list_per_minute_dict = {}
        self.charging_list_per_minute_dict = {}
        self.already_charged_list_per_minute_dict = {}
        # available_solar_power_per_bev = available_solar_power / waiting_bevs (bei Durchlauf ohne charging BEVs)
        self.available_solar_power_per_bev_per_minute_dict = {}
        self.unused_solar_energy = 0

    def add_available_solar_power_per_bev_to_dict(self, minute, available_solar_power_per_bev):
        self.available_solar_power_per_bev_per_minute_dict[minute] = round(available_solar_power_per_bev, 2)

    def add_waiting_list_to_dict(self, minute, waiting_list):
        self.waiting_list_per_minute_dict[minute] = waiting_list

    def get_waiting_list_per_minute_dict(self):
        return self.waiting_list_per_minute_dict

    def add_charging_list_to_dict(self, minute, charging_list):
        self.charging_list_per_minute_dict[minute] = charging_list

    def get_charging_list_per_minute_dict(self):
        return self.charging_list_per_minute_dict

    def add_already_charged_list_to_dict(self, minute, already_charged_list):
        self.already_charged_list_per_minute_dict[minute] = already_charged_list

    def get_already_charged_list_per_minute_dict(self):
        return self.already_charged_list_per_minute_dict

    def add_unused_solar_energy(self, unused_solar_energy):
        self.unused_solar_energy += unused_solar_energy

    def get_total_number_of_unused_solar_energy(self):
        return self.unused_solar_energy


class BevData:

    def __init__(self):
        self.bev_data_per_minute_dict = {}
        # Charging power für ein BEV
        self.charging_power_per_bev_per_minute_dict = {}
        self.total_number_of_charged_bevs = 0
        self.sum_of_fueled_solar_energy = 0
        self.interrupted_charging_processes = 0
        self.bev_with_no_charging_slot_in_forecast = 0

    def add_bev_data_per_minute_dict(self, minute, current_bevs_dict):
        self.bev_data_per_minute_dict[minute] = current_bevs_dict

    def get_bev_data_per_minute_dict(self, minute):
        return self.bev_data_per_minute_dict[minute].get_bevs_dict()

    def add_charging_power_per_bev_per_minute_dict(self, id_bev, minute, charging_power_for_bev_for_minute):
        if id_bev in self.charging_power_per_bev_per_minute_dict:
            self.charging_power_per_bev_per_minute_dict[id_bev][minute] = charging_power_for_bev_for_minute
        else:
            self.charging_power_per_bev_per_minute_dict[id_bev] = {}
            self.charging_power_per_bev_per_minute_dict[id_bev][minute] = charging_power_for_bev_for_minute

    def get_charging_power_per_bev_per_minute_dict(self, id_bev, minute):
        return self.charging_power_per_bev_per_minute_dict[id_bev][minute]

    def get_bev_dict_for_last_minute(self):
        return list(self.bev_data_per_minute_dict.values())[-1].get_bevs_dict()

    def get_total_number_of_charged_bevs(self):
        return self.total_number_of_charged_bevs

    def get_total_number_of_fueled_solar_energy(self):
        return round(self.sum_of_fueled_solar_energy, 2)

    def get_number_of_bev_with_no_charging_slot_in_forecast(self):
        return self.bev_with_no_charging_slot_in_forecast

    def increase_number_of_bev_with_no_charging_slot_in_forecast(self):
        self.bev_with_no_charging_slot_in_forecast += 1

    def increase_number_of_interrupted_charging_processes(self):
        self.interrupted_charging_processes += 1

    def get_number_of_interrupted_charging_processes(self):
        return self.interrupted_charging_processes

    def set_total_number_of_charged_bevs(self):
        bev_dict_for_last_minute = self.get_bev_dict_for_last_minute()
        for bev_data in bev_dict_for_last_minute.values():
            self.total_number_of_charged_bevs += get_charging_status_of_bev(bev_data)

    def set_total_number_of_fueled_solar_energy(self):
        bev_dict_for_last_minute = self.get_bev_dict_for_last_minute()
        for bev_data in bev_dict_for_last_minute.values():
            self.sum_of_fueled_solar_energy += get_fueled_solar_energy_per_bev(bev_data)


class TableDict:

    def __init__(self):
        self.table_dict = {}

    def add_table(self, minute, current_table):
        self.table_dict[minute] = current_table

    def get_table(self, minute):
        return self.table_dict[minute]

    def show_table(self, minute):
        fig = self.table_dict[minute]
        fig.show()


def safe_bev_dict_per_minute(minute, simulation_day, bev_data, table_dict, solar_peak_power):
    current_bevs_dict = copy.deepcopy(simulation_day.bevs_dict)
    bev_data.add_bev_data_per_minute_dict(minute, current_bevs_dict)
    bev_dict_specific_minute = bev_data.get_bev_data_per_minute_dict(minute)
    current_table = create_plotly_table(bev_dict_specific_minute, solar_peak_power,
                                        minute)
    table_dict.add_table(minute, current_table)


def safe_bev_dict_per_minute_forecast(minute, simulation_day, bev_data, table_dict, available_solar_power):
    current_bevs_dict = copy.deepcopy(simulation_day.bevs_dict)
    bev_data.add_bev_data_per_minute_dict(minute, current_bevs_dict)
    bev_dict_specific_minute = bev_data.get_bev_data_per_minute_dict(minute)
    current_table = create_plotly_table_forecast(bev_dict_specific_minute, available_solar_power)
    table_dict.add_table(minute, current_table)


def safe_waiting_list_per_minute(simulation_day, simulation_data, minute):
    waiting_list = copy.deepcopy(simulation_day.waiting_bevs_list.get_waiting_bevs_list())
    simulation_data.add_waiting_list_to_dict(minute, waiting_list)


def safe_available_solar_power_per_bev_per_minute(simulation_data, minute, available_solar_power):
    number_of_waiting_bevs = len(simulation_data.waiting_list_per_minute_dict[minute])
    available_solar_power_per_minute = calculate_available_solar_power_per_bev(available_solar_power, number_of_waiting_bevs)
    simulation_data.add_available_solar_power_per_bev_to_dict(minute, available_solar_power_per_minute)


def safe_charging_list_per_minute(charging_list_to_safe, simulation_data, minute):
    simulation_data.add_charging_list_to_dict(minute, charging_list_to_safe)


def get_fueled_solar_energy_per_bev(bev_data):
    fueled_solar_energy_per_bev = 0
    for charging_tuple in bev_data[2]:
        fueled_solar_energy_per_bev += charging_tuple[2]
    return fueled_solar_energy_per_bev


def get_charging_status_of_bev(bev_data):
    if len(bev_data[2]) != 0:
        return 1
    return 0


def create_plotly_table(bev_dict_specific_minute, solar_peak_power, minute):
    parking_states = []
    parking_starts = []
    parking_duration = []
    number_of_charges = []
    charging_start = []
    charging_time = []
    fueled_solar_energy = []

    for id_bev in bev_dict_specific_minute.keys():
        bev_data = bev_dict_specific_minute[id_bev]
        parking_states.append(bev_data[1])
        parking_starts.append(as_time_of_day_from_hour(bev_data[0][0]))
        parking_duration.append(bev_data[0][1])
        fueled_solar_energy_sum = 0
        number_of_charges_value = 0
        charging_tuple_start = []
        charging_tuple_time = []
        for charging_tuple in bev_data[2]:
            charging_tuple_start.append(as_time_of_day_from_minute(charging_tuple[0]))
            charging_tuple_time.append(charging_tuple[1])
            fueled_solar_energy_sum += charging_tuple[2]
            number_of_charges_value += 1
        fueled_solar_energy.append(round(fueled_solar_energy_sum, 2))
        number_of_charges.append(number_of_charges_value)
        charging_start.append(charging_tuple_start)
        charging_time.append(charging_tuple_time)

    available_solar_power = get_available_solar_power_linear_interpolated(solar_peak_power, minute)

    fig = go.Figure(
        data=[go.Table(header=dict(values=['ID BEV', 'Zustand', 'Parkstart', 'Parkdauer in h', 'Anzahl Aufladungen',
                                           'Ladestart', 'Ladedauer in min', 'Getankte Solarenergie in kWh']),
                       cells=dict(values=[[id_bev for id_bev in bev_dict_specific_minute.keys()],
                                          [item for item in parking_states],
                                          [item for item in parking_starts],
                                          [item for item in parking_duration],
                                          [item for item in number_of_charges],
                                          [item for item in charging_start],
                                          [item for item in charging_time],
                                          [item for item in fueled_solar_energy],
                                          ],
                                  fill=dict(color=[[
                                      'lightgray' if state == 'nicht parkend' else 'lightyellow' if state == 'wartend' else 'palegreen'
                                      for state in parking_states]]
                                  )))
              ])

    fig.update_layout(width=1000, height=900, title_text='{} kW verfügbare Solarleistung'.format(available_solar_power))

    return fig


def create_plotly_table_forecast(bev_dict_specific_minute, available_solar_power):
    parking_states = []
    parking_starts = []
    parking_duration = []
    charging_start = []
    charging_time = []
    fueled_solar_energy = []
    fair_share_charging_energy = []

    for id_bev in bev_dict_specific_minute.keys():
        bev_data = bev_dict_specific_minute[id_bev]
        parking_states.append(bev_data[1])
        parking_starts.append(as_time_of_day_from_hour(bev_data[0][0]))
        parking_duration.append(bev_data[0][1])
        fair_share_charging_energy.append(round(bev_data[3][0], 2))
        fueled_solar_energy_sum = 0
        number_of_charges_value = 0
        charging_tuple_start = []
        charging_tuple_time = []
        for charging_tuple in bev_data[2]:
            charging_tuple_start.append(as_time_of_day_from_minute(charging_tuple[0]))
            charging_tuple_time.append(round(charging_tuple[1], 2))
            fueled_solar_energy_sum += charging_tuple[2]
            number_of_charges_value += 1
        fueled_solar_energy.append(round(fueled_solar_energy_sum, 2))
        charging_start.append(charging_tuple_start)
        charging_time.append(charging_tuple_time)

    fig = go.Figure(
        data=[go.Table(header=dict(values=['ID BEV', 'Zustand', 'Parkstart', 'Parkdauer in h', 'Ladestart',
                                           'Ladedauer in min', 'Getankte Solarenergie in kWh', 'Fairer Solarenergie Anteil in kWh']),
                       cells=dict(values=[[id_bev for id_bev in bev_dict_specific_minute.keys()],
                                          [item for item in parking_states],
                                          [item for item in parking_starts],
                                          [item for item in parking_duration],
                                          [item for item in charging_start],
                                          [item for item in charging_time],
                                          [item for item in fueled_solar_energy],
                                          [item for item in fair_share_charging_energy],
                                          ],
                                  fill=dict(color=[[
                                      'lightgray' if state == 'nicht parkend' else 'lightyellow' if state == 'wartend' else 'palegreen'
                                      for state in parking_states]]
                                  )))
              ])

    fig.update_layout(width=1000, height=900, title_text='{} kW verfügbare Solarleistung (Intervallmitte)'.format(available_solar_power))

    return fig