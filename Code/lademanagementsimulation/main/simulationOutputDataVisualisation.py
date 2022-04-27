from IPython.display import Markdown as md
from ipywidgets import IntSlider, interact


def print_algorithm_result(bev_data, simulation_data, anzahl_bevs_pro_tag):
    bev_data.set_total_number_of_fueled_solar_energy()
    bev_data.set_total_number_of_charged_bevs()
    total_number_of_fueled_solar_energy = bev_data.get_total_number_of_fueled_solar_energy()
    total_number_of_charged_bevs = bev_data.get_total_number_of_charged_bevs()
    number_of_interrupted_charging_processes = bev_data.get_number_of_interrupted_charging_processes()
    total_number_of_unused_solar_energy = simulation_data.get_total_number_of_unused_solar_energy()
    return md(">**Ergebnis**<br>Geladene BEVs: {} von {}<br>Unterbrochene Aufladevorgänge {}<br>Aufgeladene Solarenergie insgesamt: {} kWh<br>Ungenutzte Solarenergie insgesamt: {} kWh".format(
        total_number_of_charged_bevs, anzahl_bevs_pro_tag, number_of_interrupted_charging_processes,
        total_number_of_fueled_solar_energy, total_number_of_unused_solar_energy))


def create_tabular_overview_per_minute_slider(table_dict, minute_interval):
    slider = IntSlider(value=480, min=480, max=960, step=minute_interval, description='Minute: ')
    # minute = slider.value
    interact(table_dict.show_table, minute=slider)
