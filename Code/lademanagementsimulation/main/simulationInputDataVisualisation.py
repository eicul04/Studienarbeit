import pandas as pd
import plotly.express as px
from dash import dcc
from dash import html
from dash.dependencies import Input, Output  # Load Data
from jupyter_dash import JupyterDash

import figureGeneration
import data


def create_jupyter_dash_app(solar_peak_power):
    app = JupyterDash(__name__)

    # Daten holen
    df_solar_radiation = data.get_solar_radiation_dataframe()
    df_electricity_own_consumption = data.get_electricity_own_consumption()
    df_solar_power = data.get_solar_power_dataframe(solar_peak_power)


    app.layout = html.Div(
        children=[
            dcc.Checklist(
                id='options',
                options=[
                    {'label': 'Solarleistung', 'value': 'Solarleistung'},
                    {'label': 'Stromeigenverbrauch DHBW Karlsruhe', 'value': 'Stromeigenverbrauch'},
                ],
                value=[],
            ),
            dcc.Graph(id='graph-simulation'),
        ]

    )

    @app.callback(Output(component_id='graph-simulation', component_property='figure'),
                  [Input(component_id='options', component_property='value')])
    def update_graph(input_value):
        graph = px.line()
        for element in input_value:
            if element == 'Solarleistung':
                graph.add_scatter(x=df_solar_power['Uhrzeit'], y=df_solar_power['Solarleistung'],
                                  line_color='blue', name='Solarleistung')
            elif element == 'Stromeigenverbrauch':
                graph.add_scatter(x=df_electricity_own_consumption['Uhrzeit'],
                                  y=df_electricity_own_consumption['Stromeigenverbrauch'],
                                  line_color='red', name='Stromeigenverbrauch')

        graph.update_layout(template='plotly_white',
                            yaxis={'title': 'Leistung in kW'},
                            xaxis={'title': 'Uhrzeit'},
                            title={'text': 'Simulation Eingangsdaten',
                                   'font': {'size': 24}, 'x': 0.5, 'xanchor': 'center'})
        return graph

    # Run app and display result inline in the notebook
    app.run_server(mode='inline')
