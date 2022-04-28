import calculation
import pandas as pd
import numpy as np
import scipy as sp
import scipy.interpolate

from timeTransformation import df_in_minutes, as_time_of_day_from_minute, transform_to_minutes


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


def get_available_solar_energy_dataframe_interpolated(solar_peak_power):
    df_available_solar_power = get_available_solar_power_dataframe_interpolated(solar_peak_power)
    df_available_solar_power = df_available_solar_power.reset_index()  # make sure indexes pair with number of rows
    for index, row in df_available_solar_power.iterrows():
        df_available_solar_power.at[index, 'Verfügbare Solarleistung'] = row['Verfügbare Solarleistung'] * 1/60
    df_available_solar_power.rename(columns={"Verfügbare Solarleistung": "Verfügbare Solarenergie"}, inplace=True)
    return df_available_solar_power


def get_available_solar_power_dataframe_interpolated(solar_peak_power):
    # Get data
    time_original_in_minutes = transform_to_minutes(get_available_solar_power_dataframe(solar_peak_power)['Uhrzeit'])
    available_solar_power_original = get_available_solar_power_dataframe(solar_peak_power)[
        'Verfügbare Solarleistung']

    time_in_minute_steps = np.arange(start=time_original_in_minutes.min(), stop=time_original_in_minutes.max() + 1,
                                     step=1)

    # Quadratic Interpolation
    quadratic_interpolation = sp.interpolate.interp1d(time_original_in_minutes, available_solar_power_original,
                                                      kind='quadratic', fill_value="extrapolate")
    available_solar_power_interpolated = quadratic_interpolation(time_in_minute_steps)

    return pd.DataFrame(
        list(zip(time_in_minute_steps, available_solar_power_interpolated)),
        columns=["Minuten", "Verfügbare Solarleistung"])


def get_available_solar_power_dataframe_linear_interpolated(solar_peak_power, minute_interval):
    # Get data
    time_original_in_minutes = transform_to_minutes(get_available_solar_power_dataframe(solar_peak_power)['Uhrzeit'])
    available_solar_power_original = get_available_solar_power_dataframe(solar_peak_power)[
        'Verfügbare Solarleistung']

    time_in_minute_interval_steps = np.arange(start=time_original_in_minutes.min(), stop=time_original_in_minutes.max() + 1,
                                     step=minute_interval)

    # Linear Interpolation
    linear_interpolation = sp.interpolate.interp1d(time_original_in_minutes, available_solar_power_original,
                                                      kind='linear', fill_value="extrapolate")
    available_solar_power_interpolated = linear_interpolation(time_in_minute_interval_steps)

    return pd.DataFrame(
        list(zip(time_in_minute_interval_steps, available_solar_power_interpolated)),
        columns=["Minuten", "Verfügbare Solarleistung"])


def get_available_solar_power(solar_peak_power, minute):
    return calculation.get_available_solar_power_quadratic_interpolated(solar_peak_power, minute)


def get_available_solar_power_in_minute_interval_start(solar_peak_power, minute):
    return calculation.get_available_solar_power_linear_interpolated(solar_peak_power, minute)

def get_available_solar_energy(solar_peak_power, minute):
    available_solar_power = get_available_solar_power(solar_peak_power, minute)
    return available_solar_power * (1/60)


def get_probability_arrival_time_bevs():
    df_probability_arrival_time_bev = pd.read_csv('data_files/wahrscheinlichkeit_ankunftszeit.csv', sep=';')
    return df_probability_arrival_time_bev
