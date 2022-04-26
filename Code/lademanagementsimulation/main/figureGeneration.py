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


def create_charging_power_figure(simulation_day):
    add_rectangles_to_charging_power_figure_forecast(simulation_day)
    generate_charging_power_figure()


# TODO bei prognose Algorithmus untere Funktion => schöner machen
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


# TODO ID auf rectangle schreiben
def add_rectangles_to_charging_power_figure_forecast(simulation_day):
    charging_starts_with_associated_bev_ids = get_charging_start_with_associated_bev_ids(simulation_day)
    print(charging_starts_with_associated_bev_ids)
    for charging_start in charging_starts_with_associated_bev_ids.keys():
        ids_bev_with_same_charging_start = list(charging_starts_with_associated_bev_ids[charging_start])
        start_height = 0
        for id_bev in ids_bev_with_same_charging_start:
            print(ids_bev_with_same_charging_start, "IDs BEV with same charging start")
            charging_end = calculate_charging_end(charging_start, simulation_day.bevs_dict.get_charging_time(id_bev))
            # TODO replace Mock
            charging_energy = 1
            draw_rectangle(charging_start, start_height, charging_end, start_height + charging_energy)
            start_height += charging_energy
        print(start_height, "Start Höhe")


def stack_rectangles_with_same_charging_start():
    print("stacked")


def draw_rectangle(x0, y0, x1, y1):
    return ladestrom_bev_fig.add_shape(type="rect",
                                       x0=x0, y0=y0, x1=x1, y1=y1,
                                       line=dict(color="green"),
                                       )


def generate_charging_power_figure():
    global ladestrom_bev_fig

    # Set axes properties
    ladestrom_bev_fig.update_xaxes(range=[480, 960], showgrid=True)
    ladestrom_bev_fig.update_yaxes(range=[0, 10])

    ladestrom_bev_fig.update_shapes(dict(xref='x', yref='y'))
    ladestrom_bev_fig.update_layout(yaxis={'title': 'Energie in kWh'},
                                    xaxis={'title': 'Minuten'},
                                    title={'text': 'Ladeenergie pro Ladezeitraum eines BEVs',
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
