import plotly.graph_objects as go

import data
from timeTransformation import as_time_of_day_from_hour, as_time_of_day_from_minute


class VisualisationObject:

    def __init__(self):
        self.bev_dict_per_minute = {}

    def add_bev_dict(self, minute, current_bevs_dict):
        self.bev_dict_per_minute[minute] = current_bevs_dict

    def get_bev_dict(self, minute):
        return self.bev_dict_per_minute[minute].get_bevs_dict()


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

    available_solar_power = data.get_available_solar_power(solar_peak_power, minute)

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
