from collections import OrderedDict

import pandas as pd
import plotly.express as px
import numpy as np
import scipy as sp
import scipy.interpolate
from matplotlib import pyplot as plt
import data
import plotly.graph_objects as go
from itertools import chain

from timeTransformation import transform_to_minutes
from simulationService import calculate_charging_end

ladestrom_bev_fig = go.Figure()


def create_available_solar_power_figure(solar_peak_power):
    df_verfuegbarer_solarstrom = data.get_available_solar_power_dataframe(solar_peak_power)
    available_solar_power_fig = px.line(df_verfuegbarer_solarstrom, x='Uhrzeit', y='Verfügbare Solarleistung')
    return available_solar_power_fig


def get_data_frame_for_charging_power_per_bev(charging_power_per_bev_per_minute_dict, id_bev):
    charging_power_per_minute_dict = charging_power_per_bev_per_minute_dict[id_bev]
    return pd.DataFrame.from_dict(charging_power_per_minute_dict, orient='index', columns=['Ladeleistung'])


# TODO ACHTUNG bei Prognose Algorithmus untere Funktion verwenden
def add_rectangles_to_charging_power_figure(simulation_day):
    for id_bev in simulation_day.bevs_dict.get_bevs_dict():
        for charging_tuple in simulation_day.bevs_dict.get_charging_data(id_bev):
            # x0 = charging_start, x1 = charging_end (charging_start + charging_time),
            # y0 = 0 oder stromeigenverbrauch, y1 = charging_energy oder stromeigenverbrauch + charging_energy
            charging_start = charging_tuple[0]
            charging_time = charging_tuple[1]
            charging_end = calculate_charging_end(charging_start, charging_time)
            charging_energy = charging_tuple[2]
            draw_rectangle(charging_start, 0, charging_end, charging_energy)


def get_charging_start_with_associated_bev_ids(simulation_day):
    charging_starts_with_associated_bev_ids = {}
    for key, value in simulation_day.bevs_dict.get_bevs_dict().items():
        charging_starts_with_associated_bev_ids.setdefault(value[2][0][0], set()).add(key)
    # result = set(chain.from_iterable(values for key, values in charging_starts_with_associated_bev_ids.items()
    #             if len(values) > 1))
    return charging_starts_with_associated_bev_ids


# TODO wenn bereits bev-rectangle gezeichnet und dann kommt anderes bev-rectangle dazu,
#  dann wird die Höhe vom ersten bev-rectangle um die Hälfte verkürzt
def add_rectangles_to_charging_power_figure_forecast(simulation_day, solar_peak_power):
    start_height = 0
    rectangle_height = 0
    # {id: charging_end}
    drawn_rectangles_to_check = {}
    charging_starts_with_associated_bev_ids = get_charging_start_with_associated_bev_ids(simulation_day)
    charging_starts_with_associated_bev_ids_ordered_by_start = OrderedDict(
        sorted(charging_starts_with_associated_bev_ids.items()))
    for charging_start in charging_starts_with_associated_bev_ids_ordered_by_start.keys():
        ids_bev_with_same_charging_start = list(charging_starts_with_associated_bev_ids[charging_start])
        for id_bev in ids_bev_with_same_charging_start:
            charging_tuple = simulation_day.bevs_dict.get_charging_data(id_bev)
            charging_start = charging_tuple[0][0]
            charging_time = charging_tuple[0][1]
            charging_end = calculate_charging_end(charging_start, charging_time)
            charging_energy = charging_tuple[0][2]

            rectangles_already_on_stack = \
                dict((key, value) for key, value in drawn_rectangles_to_check.items() if value[0] >= charging_start)
            print(rectangles_already_on_stack, "rectangles_already_on_stack")

            available_solar_energy_for_start = data.get_available_solar_energy(solar_peak_power, charging_start)
            number_of_rectangles_already_on_stack = len(rectangles_already_on_stack)

            start_height = get_start_height(start_height, rectangle_height, number_of_rectangles_already_on_stack)
            rectangle_height = get_rectangle_height(available_solar_energy_for_start,
                                                    number_of_rectangles_already_on_stack)

            # update_rectangle_height(drawn_rectangles_to_check, rectangle_height)

            # TODO update gezeichnete rectangles

            draw_rectangle(charging_start, start_height, charging_end, start_height + rectangle_height)
            add_id_on_rectangle(charging_start, start_height, id_bev)
            drawn_rectangles_to_check[id_bev] = (charging_end, rectangle_height)


def get_start_height(start_height, rectangle_height, number_of_rectangles_already_on_stack):
    if number_of_rectangles_already_on_stack == 1:
        start_height += rectangle_height
    elif number_of_rectangles_already_on_stack > 1:
        start_height += rectangle_height / number_of_rectangles_already_on_stack
    else:
        start_height = 0
    return start_height


# TODO available_solar_energy_for_start durch charging_energy_per_minute ersetzen (für minute nicht der aufaddierte Wert
#  aus dem BEV dict)
def get_rectangle_height(available_solar_energy_for_start, number_of_rectangles_already_on_stack):
    if number_of_rectangles_already_on_stack > 0:
        rectangle_height = available_solar_energy_for_start / number_of_rectangles_already_on_stack
    else:
        rectangle_height = available_solar_energy_for_start
    return rectangle_height


def get_number_of_changes_of_charging_power(charging_power_per_minute_dict):
    list_of_charging_power_values = []
    for value in charging_power_per_minute_dict.values():
        list_of_charging_power_values.append(value)
    return (np.diff(list_of_charging_power_values) != 0).sum()


def get_values_if_change(charging_power_per_minute_dict):
    ordered_charging_power_per_minute_dict = OrderedDict(charging_power_per_minute_dict)
    for minute in charging_power_per_minute_dict.keys():
        # next_key, key = ordered_charging_power_per_minute_dict._OrderedDict__map[minute]
        return "nothing"


def get_points_of_rectangle_with_stages(bev_data):
    # rectangle_height_1 = bev_data.get_charging_power_for_minute(charging_start)
    # rectangle_height_ = bev_data.get_charging_power_for_minute(change_in_charging_power_1)...
    x = []
    y = []
    return "nothing"


# TODO delete this method
def update_rectangle_height(drawn_rectangles_to_check, rectangle_height):
    for id_bev in drawn_rectangles_to_check.keys():
        drawn_rectangles_to_check[id_bev][0][1] = rectangle_height


def draw_rectangle(x0, y0, x1, y1):
    return ladestrom_bev_fig.add_shape(type="rect",
                                       x0=x0, y0=y0, x1=x1, y1=y1,
                                       line=dict(color="green"),
                                       )


def draw_rectangle_with_stage():
    return go.Scatter(x=[0, 1, 2, 0], y=[0, 2, 0, 0], fill="toself")


def add_id_on_rectangle(x0, y0, id_bev):
    # Adding a trace with a fill, setting opacity to 0
    ladestrom_bev_fig.add_trace(
        go.Scatter(
            x=[x0 + 2],
            y=[y0 + 0.5],
            text='{}'.format(id_bev),
            mode='text',
        )
    )


def create_charging_power_figure(simulation_day, solar_peak_power, bev_data, minute_interval):
    # add_rectangles_to_charging_power_figure_forecast(simulation_day, solar_peak_power)
    df_available_solar_power = data.get_available_solar_power_dataframe_linear_interpolated(solar_peak_power, minute_interval)
    charging_power_per_bev_per_minute_dict = bev_data.charging_power_per_bev_per_minute_dict
    # number_of_stages = get_number_of_changes_of_charging_power(charging_power_per_bev_per_minute_dict)
    rectangle_points = get_points_of_rectangle_with_stages(bev_data)
    generate_charging_power_figure(df_available_solar_power, charging_power_per_bev_per_minute_dict)


def generate_charging_power_figure(df_available_solar_energy, charging_power_per_bev_per_minute_dict):
    global ladestrom_bev_fig

    # Set axes properties
    ladestrom_bev_fig.update_xaxes(range=[480, 960], showgrid=True)
    ladestrom_bev_fig.update_yaxes(range=[0, 60])

    # ladestrom_bev_fig.update_shapes(dict(xref='x', yref='y'))

    ladestrom_bev_fig.add_scatter(x=df_available_solar_energy['Minuten'],
                                  y=df_available_solar_energy['Verfügbare Solarleistung'],
                                  line_color='orange', name='Verfügbare Solarleistung')

    for id_bev in charging_power_per_bev_per_minute_dict.keys():
        df_bev = get_data_frame_for_charging_power_per_bev(charging_power_per_bev_per_minute_dict, id_bev)

        ladestrom_bev_fig.add_scatter(x=df_bev.index,
                                      y=df_bev['Ladeleistung'],
                                      line_color='blue', name='ID BEV {}'.format(id_bev))

    ladestrom_bev_fig.update_layout(yaxis={'title': 'Energie in kW'},
                                    xaxis={'title': 'Minuten'},
                                    title={'text': 'Ladeleistung pro Ladezeitraum eines BEVs',
                                           'font': {'size': 24}, 'x': 0.5, 'xanchor': 'center'},
                                    template='plotly_white')
    ladestrom_bev_fig.show()


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
                                  line_color='orange', name='Wartende BEVs')

    bev_number_figure.add_scatter(x=df_charging_bevs['Minuten'], y=df_charging_bevs['Ladende BEVs'],
                                  line_color='green', name='Ladende BEVs')

    bev_number_figure.update_layout(yaxis={'title': 'Anzahl BEVs'},
                                    xaxis={'title': 'Minuten'},
                                    title={'text': 'Anzahl wartender und ladender BEVs im Tagesverlauf',
                                           'font': {'size': 24}, 'x': 0.5, 'xanchor': 'center'},
                                    template='plotly_white')

    bev_number_figure.show()


def create_available_solar_power_figure_quadratic_interpolation(solar_peak_power):
    # Get data
    time_original_in_minutes = transform_to_minutes(
        data.get_available_solar_power_dataframe(solar_peak_power)['Uhrzeit'])
    available_solar_power_original = data.get_available_solar_power_dataframe(solar_peak_power)[
        'Verfügbare Solarleistung']

    # Plot data
    plt.rcParams["figure.figsize"] = [8.50, 4.00]
    plt.rcParams["figure.autolayout"] = True
    fig, graph = plt.subplots()
    graph.scatter(time_original_in_minutes, available_solar_power_original, c='red', lw=2, label='original datapoints')

    # TODO nicht in Stunden sondern in Minuten konvertieren
    # Create time_in_minute_steps Datapoints
    time_in_minute_steps = np.arange(start=time_original_in_minutes.min(), stop=time_original_in_minutes.max() + 1,
                                     step=1)

    # Quadratic Interpolation
    quadratic_interpolation = sp.interpolate.interp1d(time_original_in_minutes, available_solar_power_original,
                                                      kind='quadratic', fill_value="extrapolate")
    available_solar_power_interpolated = quadratic_interpolation(time_in_minute_steps)

    # Add time_in_minute_steps, vquadratic line to existing plot
    graph.plot(time_in_minute_steps, available_solar_power_interpolated, color='green', linestyle=':',
               label='quadratic interpolation')
    graph.legend(loc='upper left')
    graph.set_xlabel('Minuten')
    graph.set_ylabel('Verfügbare Solarleistung in kW')
    plt.show()
