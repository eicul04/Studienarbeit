from collections import OrderedDict
from collections import defaultdict
from operator import getitem

import pandas as pd
import plotly.express as px
import data
import plotly.graph_objects as go

from calculation import get_available_solar_power_linear_interpolated

ladestrom_bev_fig = go.Figure()


def create_available_solar_power_figure(solar_peak_power):
    df_verfuegbarer_solarstrom = data.get_available_solar_power_dataframe(solar_peak_power)
    available_solar_power_fig = px.line(df_verfuegbarer_solarstrom, x='Uhrzeit', y='Verfügbare Solarleistung')
    return available_solar_power_fig


def get_data_frame_for_charging_power_per_bev(charging_power_per_bev_per_minute_dict, id_bev):
    charging_power_per_minute_dict = charging_power_per_bev_per_minute_dict[id_bev]
    return pd.DataFrame.from_dict(charging_power_per_minute_dict, orient='index', columns=['Ladeleistung'])


def create_probability_arriving_time_figure():
    df_probability_arrival_times = data.get_probability_arrival_time_bevs()
    df_probability_arrival_times['Wahrscheinlichkeit Anzahl ankommende BEVs'] = df_probability_arrival_times['Wahrscheinlichkeit Anzahl ankommende BEVs'].transform(lambda x: x * 100)
    fig = px.bar(df_probability_arrival_times, x='Uhrzeit', y='Wahrscheinlichkeit Anzahl ankommende BEVs')
    fig.update_layout(yaxis={'title': 'Wahrscheinlichkeit Anzahl ankommende BEVs in %'},
                                    xaxis={'title': 'Uhrzeit'},
                                    title={'text': 'Wahrscheinlichkeiten Ankunftszeiten',
                                           'font': {'size': 24}, 'x': 0.5, 'xanchor': 'center'},
                                    template='plotly_white')
    fig.show()


def create_charging_power_figure(simulation_day, solar_peak_power, bev_data, minute_interval):
    df_available_solar_power = data.get_available_solar_power_dataframe_linear_interpolated(solar_peak_power,
                                                                                            minute_interval)
    charging_power_per_bev_per_minute_dict = bev_data.charging_power_per_bev_per_minute_dict
    generate_charging_power_figure(df_available_solar_power, charging_power_per_bev_per_minute_dict, solar_peak_power)


def generate_charging_power_figure(df_available_solar_energy, charging_power_per_bev_per_minute_dict, solar_peak_power):
    global ladestrom_bev_fig

    # Set axes properties
    ladestrom_bev_fig.update_xaxes(range=[480, 960], showgrid=True)
    ladestrom_bev_fig.update_yaxes(range=[0, 60])

    ladestrom_bev_fig.add_scatter(x=df_available_solar_energy['Minuten'],
                                  y=df_available_solar_energy['Verfügbare Solarleistung'],
                                  line_color='orange', name='Verfügbare Solarleistung')

    # print(charging_power_per_bev_per_minute_dict)

    # sort because minutes from optimization reversed
    for id_bev, charging_power_per_minute in charging_power_per_bev_per_minute_dict.items():
        charging_power_per_bev_per_minute_dict[id_bev] = OrderedDict(sorted(charging_power_per_minute.items()))

    charging_power_per_bev_per_minute_dict_manipulated_for_visualisation = \
        manipulate_data_frame_to_stack_diagrams(charging_power_per_bev_per_minute_dict, solar_peak_power)

    for id_bev, charging_power_per_minute in charging_power_per_bev_per_minute_dict_manipulated_for_visualisation.items():
        minutes_for_id_bev = []
        charging_power_per_minute_for_id_bev = []
        for minute in charging_power_per_minute.keys():
            minutes_for_id_bev.append(minute)
            charging_power_per_minute_for_id_bev.append(charging_power_per_minute[minute])

        df_bev = get_data_frame_for_charging_power_per_bev(
            charging_power_per_bev_per_minute_dict_manipulated_for_visualisation,
            id_bev)

        df_bev.loc[minutes_for_id_bev[0]] = [0]
        df_bev_zero_values = pd.DataFrame([[charging_power_per_minute_for_id_bev[0]], [0]], columns=['Ladeleistung'],
                                          index=[minutes_for_id_bev[0], minutes_for_id_bev[-1]])

        df_bev = df_bev.append(df_bev_zero_values)
        df_bev.index = df_bev.index + 0  # shifting index
        df_bev = df_bev.sort_index()

        ladestrom_bev_fig.add_scatter(x=df_bev.index,
                                      y=df_bev['Ladeleistung'],
                                      line_color='green', mode='lines', name='ID BEV {}'.format(id_bev))

    ladestrom_bev_fig.update_layout(yaxis={'title': 'Energie in kW'},
                                    xaxis={'title': 'Minuten'},
                                    title={'text': 'Ladeleistung pro Ladezeitraum eines BEVs',
                                           'font': {'size': 24}, 'x': 0.5, 'xanchor': 'center'},
                                    template='plotly_white')
    ladestrom_bev_fig.show()


def manipulate_data_frame_to_stack_diagrams(charging_power_per_bev_per_minute_dict, solar_peak_power):
    previous_sums = defaultdict(int)

    for id_bev, charging_power_per_minute in charging_power_per_bev_per_minute_dict.items():
        for minute in charging_power_per_minute.keys():
            stacked_charging_power_per_minute = charging_power_per_minute[minute] + previous_sums[minute]
            available_solar_power = get_available_solar_power_linear_interpolated(solar_peak_power, minute)
            if stacked_charging_power_per_minute > available_solar_power + 5:
                previous_sums[minute] = charging_power_per_minute[minute]
            else:
                charging_power_per_minute[minute] += previous_sums[minute]
                previous_sums[minute] = charging_power_per_minute[minute]

    return charging_power_per_bev_per_minute_dict


def create_bev_number_figure(bev_data):
    waiting_list_per_minute_dict = bev_data.get_waiting_list_per_minute_dict()
    number_list_waiting_bevs = []
    for list_waiting_bevs in waiting_list_per_minute_dict.values():
        number_list_waiting_bevs.append(len(list_waiting_bevs))

    df_waiting_bevs = pd.DataFrame(list(zip(waiting_list_per_minute_dict.keys(), number_list_waiting_bevs)),
                                   columns=['Minuten', 'Wartende BEVs'])

    charging_list_per_minute_dict = bev_data.get_charging_list_per_minute_dict()
    number_list_charging_bevs = []
    for list_charging_bevs in charging_list_per_minute_dict.values():
        number_list_charging_bevs.append(len(list_charging_bevs))

    df_charging_bevs = pd.DataFrame(list(zip(charging_list_per_minute_dict.keys(), number_list_charging_bevs)),
                                    columns=['Minuten', 'Ladende BEVs'])

    bev_number_figure = px.line()

    bev_number_figure.add_scatter(x=df_waiting_bevs['Minuten'], y=df_waiting_bevs['Wartende BEVs'],
                                  line_color='red', name='Wartende BEVs')

    bev_number_figure.add_scatter(x=df_charging_bevs['Minuten'], y=df_charging_bevs['Ladende BEVs'],
                                  line_color='blue', name='Ladende BEVs')

    bev_number_figure.update_layout(yaxis={'title': 'Anzahl BEVs'},
                                    xaxis={'title': 'Minuten'},
                                    title={'text': 'Anzahl wartender und ladender BEVs im Tagesverlauf',
                                           'font': {'size': 24}, 'x': 0.5, 'xanchor': 'center'},
                                    template='plotly_white')

    bev_number_figure.show()
