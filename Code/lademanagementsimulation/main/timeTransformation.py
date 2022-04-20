import pandas as pd


def transform_to_hours_as_float(df_time_in_hours):
    df_pandas_date_time_format = pd.to_datetime(df_time_in_hours, format='%H:%M')
    df_date_time_format_hour = df_pandas_date_time_format.dt.hour + df_pandas_date_time_format.dt.minute / 60
    return df_date_time_format_hour


def transform_to_minutes(df_time_in_hours_and_minutes):
    df_pandas_date_time_format = pd.to_datetime(df_time_in_hours_and_minutes, format='%H:%M')
    df_minutes = df_pandas_date_time_format.dt.hour * 60 + df_pandas_date_time_format.dt.minute
    return df_minutes


def in_minutes(timestamp_in_hours):
    return int(timestamp_in_hours * 60)


def as_time_of_day_from_hour(timestamp_in_hours):
    hours = int(timestamp_in_hours)
    minutes = int((timestamp_in_hours * 60) % 60)
    return "%d:%02d Uhr" % (hours, minutes)


def as_time_of_day_from_minute(timestamp_in_minutes):
    hours = int(timestamp_in_minutes/60)
    minutes = int(timestamp_in_minutes % 60)
    return "%d:%02d" % (hours, minutes)


def df_in_minutes(df_time_in_hours):
    return df_time_in_hours * 60

