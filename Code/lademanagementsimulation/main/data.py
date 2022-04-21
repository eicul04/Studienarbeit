import calculation
import pandas as pd


class BevData:

    def __init__(self):
        self.waiting_list_per_minute_dict = {}
        self.charging_list_per_minute_dict = {}

    def add_waiting_list_to_dict(self, minute, waiting_list):
        self.waiting_list_per_minute_dict[minute] = waiting_list

    def get_waiting_list_per_minute_dict(self):
        return self.waiting_list_per_minute_dict

    def add_charging_list_to_dict(self, minute, charging_list):
        self.charging_list_per_minute_dict[minute] = charging_list

    def get_charging_list_per_minute_dict(self):
        return self.charging_list_per_minute_dict


def get_solar_radiation_dataframe():
    df_solar_radiation = pd.read_csv('data_files/sonneneinstrahlung.csv', sep=';')
    return df_solar_radiation


def get_electricity_own_consumption():
    df_electricity_own_consumption = pd.read_csv('data_files/stromeigenverbrauch.csv', sep=';')
    return df_electricity_own_consumption


def get_solar_power_dataframe(solar_peak_power):
    df_solar_power = calculation.calculate_solar_power_course(get_solar_radiation_dataframe(), solar_peak_power)
    return df_solar_power


def get_available_solar_power_dataframe(solar_peak_power):
    df_available_solar_power = calculation.calculate_available_solar_power_course(
        get_solar_power_dataframe(solar_peak_power),
        get_electricity_own_consumption())
    return df_available_solar_power


def get_available_solar_power(solar_peak_power, minute):
    return calculation.get_available_solar_power_interpolated(solar_peak_power, minute)


def get_probability_arrival_time_bevs():
    df_probability_arrival_time_bev = pd.read_csv('data_files/wahrscheinlichkeit_ankunftszeit.csv', sep=';')
    return df_probability_arrival_time_bev
