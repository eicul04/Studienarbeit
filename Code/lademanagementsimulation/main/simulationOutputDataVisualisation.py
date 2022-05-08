from IPython.display import Markdown as md
from ipywidgets import IntSlider, interact

from calculation import get_total_number_of_available_solar_energy


def print_algorithm_result(bev_data, simulation_data, anzahl_bevs_pro_tag, solar_peak_power, minute_interval):
    bev_data.set_total_number_of_fueled_solar_energy()
    bev_data.set_total_number_of_charged_bevs()
    total_number_of_available_solar_energy = get_total_number_of_available_solar_energy(solar_peak_power, minute_interval)
    total_number_of_fueled_solar_energy = bev_data.get_total_number_of_fueled_solar_energy()
    total_number_of_charged_bevs = bev_data.get_total_number_of_charged_bevs() - \
                                   bev_data.get_number_of_bev_with_no_charging_slot_in_forecast()
    # total_number_of_unused_solar_energy = simulation_data.get_total_number_of_unused_solar_energy()
    total_number_of_unused_solar_energy = round(total_number_of_available_solar_energy - total_number_of_fueled_solar_energy, 2)
    return md(
        ">**Ergebnis**<br>Geladene BEVs: {} von {}<br>Verfügbare Solarenergie insgesamt: {} kWh<br>"
        "Aufgeladene Solarenergie insgesamt: {} kWh<br>Ungenutzte Solarenergie insgesamt: {} kWh".format(
            total_number_of_charged_bevs, anzahl_bevs_pro_tag, total_number_of_available_solar_energy,
            total_number_of_fueled_solar_energy, total_number_of_unused_solar_energy))


def create_tabular_overview_per_minute_slider(table_dict, minute_interval):
    slider = IntSlider(value=480, min=480, max=960, step=minute_interval, description='Minute: ')
    # minute = slider.value
    interact(table_dict.show_table, minute=slider)
