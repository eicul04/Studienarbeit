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


def calculate_available_solar_power_per_bev(solar_peak_power, number_of_waiting_bevs, minute):
    available_solar_power = get_available_solar_power_interpolated(solar_peak_power, minute)
    if number_of_waiting_bevs != 0:
        return available_solar_power / number_of_waiting_bevs
    else:
        return 0


def get_available_solar_power_interpolated(solar_peak_power, minute):
    time_original_in_minutes = transform_to_minutes(data.get_available_solar_power_dataframe(solar_peak_power)['Uhrzeit'])
    available_solar_power_original = data.get_available_solar_power_dataframe(solar_peak_power)[
        'Verfügbare Solarleistung']

    available_solar_power_interpolated = quadratic_interpolation_for_timestamp(time_original_in_minutes, available_solar_power_original, minute)
    return available_solar_power_interpolated


def quadratic_interpolation_for_timestamp(x_values, y_values, timestamp):
    quadratic_interpolation = sp.interpolate.interp1d(x_values, y_values, kind='quadratic',
                                                      fill_value="extrapolate")
    return np.round(quadratic_interpolation(timestamp), 2)
