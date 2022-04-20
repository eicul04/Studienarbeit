from dash import Dash, Output, Input
from dash import dcc
from dash import html
import plotly.express as px
import pandas as pd

# Daten einlesen
df_sonneneinstrahlung = pd.read_csv('data_files/sonneneinstrahlung.csv', sep=';')
df_stromeigenverbrauch = pd.read_csv('data_files/stromeigenverbrauch.csv', sep=';')
df_ladestroeme = pd.read_csv('data_files/ladestroeme.csv', sep=';')
df_ladestrom_bev = pd.read_csv('data_files/ladestrom_bev.csv', sep=';')

app = Dash(__name__)


def createLadestromBevFig():
    # Mockup dataframe, muss nach Berechnungen dynamisch erzeugt werden
    ladestromBevFig = px.line(df_ladestrom_bev, x='Minuten', y='Ladeleistung')
    return ladestromBevFig


app.layout = html.Div(
    children=[
        html.H1(children="Lademanagementsimulation", ),
        dcc.Checklist(
            id='options',
            options=[
                {'label': 'Tagesverlauf Sonneneinstrahlung', 'value': 'Sonneneinstrahlung'},
                {'label': 'Stromeigenverbrauch DHBW Karlsruhe', 'value': 'Stromeigenverbrauch'},
                {'label': 'Ladeströme BEVs', 'value': 'Ladestroeme'}
            ],
            value=[],
        ),
        dcc.Graph(id='graph-simulation'),
        dcc.Graph(id='graph-ladestrom-bev', figure=createLadestromBevFig()),
    ]

)


@app.callback(Output(component_id='graph-simulation', component_property='figure'),
              [Input(component_id='options', component_property='value')])
def update_graph(input_value):
    graph = px.line()
    for element in input_value:
        if element == 'Sonneneinstrahlung':
            graph.add_scatter(x=df_sonneneinstrahlung['Minuten'], y=df_sonneneinstrahlung['Sonneneinstrahlung'],
                              line_color='blue', name='Sonneneinstrahlung')
        elif element == 'Stromeigenverbrauch':
            graph.add_scatter(x=df_stromeigenverbrauch['Minuten'], y=df_stromeigenverbrauch['Stromeigenverbrauch'],
                              line_color='red', name='Stromeigenverbrauch')
        elif element == 'Ladestroeme':
            graph.add_scatter(x=df_ladestroeme['Minuten'], y=df_ladestroeme['Ladestroeme'], line_color='green',
                              name='Ladeströme BEVs')

    graph.update_layout(template='plotly_white',
                        yaxis={'title': 'Energie'},
                        xaxis={'title': 'Minuten'},
                        title={'text': 'Titel',
                               'font': {'size': 24}, 'x': 0.5, 'xanchor': 'center'})
    return graph


if __name__ == "__main__":
    app.run_server(debug=True)


def create_dash_app_table(visualisation_object, minute):
    app = JupyterDash(__name__)

    bev_dict_specific_minute = visualisation_object.get_bev_dict(minute)

    parking_states = []
    parking_starts = []
    parking_time = []
    number_of_charges = []
    charging_start = []
    charging_time = []
    fueled_solar_energy = []

    def create_table_dataframe(dict_specific_minute):
        for id_bev in dict_specific_minute.keys():
            bev_data = bev_dict_specific_minute[id_bev]
            parking_states.append(bev_data[1])
            parking_starts.append(as_time_of_day_from_hour(bev_data[0][0]))
            parking_time.append(bev_data[0][1])
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

        # dictionary of lists
        table_dict = {'ID BEV': bev_dict_specific_minute.keys(), 'Zustand': parking_states, 'Parkstart': parking_starts,
                      'Parkdauer in h': parking_time, 'Anzahl Aufladungen': number_of_charges,
                      'Ladestart': charging_start, 'Ladedauer in min': charging_time,
                      'Getankte Solarenergie in kWh': fueled_solar_energy}

        return pd.DataFrame(table_dict)

    df = create_table_dataframe(bev_dict_specific_minute)

    app.layout = html.Div([
        dcc.Slider(min=480, max=960, step=1, value=480, id='minute-slider'),
        html.Div(id='slider-output-container'),
        html.H4('Park- und Ladezeiten Übersicht BEVs'),
        html.P(id='table_out'),
        dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            style_cell=dict(textAlign='left'),
            style_header=dict(backgroundColor="paleturquoise"),
            style_data=dict(color=[
                ['gray' if state == 'nicht parkend' else 'lightyellow' if state == 'wartend' else 'palegreen'
                 for state in parking_states]]
            )),
    ])

    @app.callback(
        Output('slider-output-container', 'children'),
        Input('minute-slider', 'value'))
    def update_output(value):
        return 'You have selected "{}"'.format(value)

    @app.callback(
        Output('table_out', 'children'),
        Input('minute-slider', 'value'))
    def update_table(value):
        bev_dict_specific_minute_new = visualisation_object.get_bev_dict(value)
        df_new = create_table_dataframe(bev_dict_specific_minute_new)
        data = df_new.to_dict('records')
        return data


    app.run_server(mode='inline')