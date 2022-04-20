import time

import pandas as pd
import plotly.express as px
import numpy as np
import scipy as sp
import scipy.interpolate
from matplotlib import pyplot as plt

import simulationManagement
import data
import timeTransformation
import plotly.graph_objects as go

ladestrom_bev_fig = go.Figure()


def create_available_solar_power_figure(solar_peak_power):
    df_verfuegbarer_solarstrom = data.get_available_solar_power_dataframe(solar_peak_power)
    available_solar_power_fig = px.line(df_verfuegbarer_solarstrom, x='Uhrzeit', y='Verfügbare Solarleistung')
    return available_solar_power_fig


def create_charging_power_figure(bev_parking_management):
    add_rectangles_to_charging_power_figure(bev_parking_management)
    generate_charging_power_figure()


def add_rectangles_to_charging_power_figure(bev_parking_management):
    for id_bev in bev_parking_management.bevs_dict.get_bevs_dict():
        for charging_tuple in bev_parking_management.bevs_dict.get_charging_data(id_bev):
            # x0 = charging_start, x1 = charging_end (charging_start + charging_time),
            # y0 = 0 oder stromeigenverbrauch, y1 = charging_energy oder stromeigenverbrauch + charging_energy
            charging_start = charging_tuple[0]
            charging_time = charging_tuple[1]
            charging_end = charging_start + charging_time
            charging_energy = charging_tuple[2]
            ladestrom_bev_fig.add_shape(type="rect",
                                        x0=charging_start, y0=0, x1=charging_end, y1=charging_energy,
                                        line=dict(color="green"),
                                        )


def generate_charging_power_figure():
    global ladestrom_bev_fig

    # Set axes properties
    ladestrom_bev_fig.update_xaxes(range=[480, 960], showgrid=True)
    ladestrom_bev_fig.update_yaxes(range=[0, 2])

    ladestrom_bev_fig.update_shapes(dict(xref='x', yref='y'))
    ladestrom_bev_fig.update_layout(yaxis={'title': 'Energie in kWh'},
                                    xaxis={'title': 'Minuten'},
                                    title={'text': 'Ladeenergie pro Ladezeitraum eines BEVs',
                                           'font': {'size': 24}, 'x': 0.5, 'xanchor': 'center'})
    ladestrom_bev_fig.show()


def create_bev_number_figure(bev_data):
    waiting_list_per_minute_dict = bev_data.get_waiting_list_per_minute_dict()
    df = pd.DataFrame(waiting_list_per_minute_dict.keys(), waiting_list_per_minute_dict.values(),
               columns =['Minuten', 'Wartende BEVs'])

    bev_number_figure = px.line()

    # TODO get Number bevs waiting, get Number bevs loading
    bev_number_figure.add_scatter(x=df['Minuten'], y=df['Wartende BEVs'],
                           line_color='blue', name='Wartende BEVs')


def create_available_solar_power_figure_quadratic_interpolation(solar_peak_power):
    # Get data
    time_original = data.get_available_solar_power_dataframe(solar_peak_power)['Uhrzeit'].dt.hour
    time_original_in_minutes = timeTransformation.df_in_minutes(time_original)
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
