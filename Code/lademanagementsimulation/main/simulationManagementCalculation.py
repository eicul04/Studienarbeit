

def calculate_unused_solar_energy(available_solar_power):
    return available_solar_power * (1 / 60)


# Returns Solarenergie in kWh (Ladeleistung * 1/60h)
# -> Ladeleistung ändert sich ggf. pro Minute, deshalb Solarenergie alle Minute berechnen
# und auf bisherige aufaddieren
def calculate_new_fueled_solar_energy(charging_power, solar_energy_fueled_so_far):
    new_solar_energy = charging_power * (1 / 60)
    return solar_energy_fueled_so_far + new_solar_energy


def calculate_parking_end(parking_start, parking_time):
    return parking_start + parking_time


def calculate_charging_time(current_minute, charging_start):
    return current_minute - charging_start


