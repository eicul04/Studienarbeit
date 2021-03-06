import pandas as pd
import numpy as np
import scipy as sp
import scipy.interpolate
import data
from timeTransformation import transform_to_minutes, df_in_minutes

list_time = ['8:00', '9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00']


def calculate_solar_power_course(df_sonneneinstrahlung, solarpeakleistung):
    df_solar_power = df_sonneneinstrahlung.copy()
    solar_power_data = calculate_solar_power(df_sonneneinstrahlung, solarpeakleistung)
    df_solar_power.update(solar_power_data)
    df_solar_power.rename(columns={"Sonneneinstrahlung": "Solarleistung"}, inplace=True)
    return df_solar_power


def calculate_solar_power(df_sonneneinstrahlung, solarpeakleistung):
    solar_power_data = (df_sonneneinstrahlung.get('Sonneneinstrahlung') / 100 * solarpeakleistung)
    return solar_power_data.transform(lambda x: int(x))


def calculate_available_solar_power_course(df_solar_power, df_electricity_own_consumption):
    df_available_solar_power = pd.DataFrame(list_time, columns=['Uhrzeit'])
    df_available_solar_power['Verfügbare Solarleistung'] = df_solar_power.get(
        'Solarleistung') - df_electricity_own_consumption.get(
        'Stromeigenverbrauch')
    return df_available_solar_power


def calculate_available_solar_power_per_bev(available_solar_power, number_of_bevs):
    if number_of_bevs != 0:
        return available_solar_power / number_of_bevs
    else:
        return 0


def transform_to_solar_energy(available_solar_power):
    return available_solar_power * (1 / 60)


def get_available_solar_power_quadratic_interpolated(solar_peak_power, minute):
    time_original_in_minutes = transform_to_minutes(
        data.get_available_solar_power_dataframe(solar_peak_power)['Uhrzeit'])
    available_solar_power_original = data.get_available_solar_power_dataframe(solar_peak_power)[
        'Verfügbare Solarleistung']

    available_solar_power_interpolated = quadratic_interpolation_for_timestamp(time_original_in_minutes,
                                                                               available_solar_power_original, minute)
    return available_solar_power_interpolated


def get_available_solar_power_linear_interpolated(solar_peak_power, minute):
    time_original_in_minutes = transform_to_minutes(
        data.get_available_solar_power_dataframe(solar_peak_power)['Uhrzeit'])
    available_solar_power_original = data.get_available_solar_power_dataframe(solar_peak_power)[
        'Verfügbare Solarleistung']

    available_solar_power_interpolated = linear_interpolation_for_timestamp(time_original_in_minutes,
                                                                            available_solar_power_original, minute)
    return available_solar_power_interpolated


def get_total_number_of_available_solar_energy(solar_peak_power, minute_interval):
    day_in_minute_interval_steps = list(range(480, 960 + 1, minute_interval))
    total_number_of_solar_energy = 0
    for minute in day_in_minute_interval_steps:
        available_solar_power = get_available_solar_power_linear_interpolated(solar_peak_power,
                                                                              minute + minute_interval / 2)
        total_number_of_solar_energy += available_solar_power * (minute_interval/60)
    return round(total_number_of_solar_energy, 2)


def quadratic_interpolation_for_timestamp(x_values, y_values, timestamp):
    quadratic_interpolation = sp.interpolate.interp1d(x_values, y_values, kind='quadratic',
                                                      fill_value="extrapolate")
    return np.round(quadratic_interpolation(timestamp), 2)


def linear_interpolation_for_timestamp(x_values, y_values, timestamp):
    linear_interpolation = sp.interpolate.interp1d(x_values, y_values, kind='linear',
                                                   fill_value="extrapolate")
    return np.round(linear_interpolation(timestamp), 2)
