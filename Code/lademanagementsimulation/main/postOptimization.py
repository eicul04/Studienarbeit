# Nachoptimierungslauf:
# Aufträge nach Abfahrtzeit absteigend sortieren
# d.h. zuerst den Auftrag der als letzter das Parkhaus verlässt.
# Dann terminieren Sie diese rückwärts (d.h. Verfahren läuft spiegelverkehrt).
# Dadurch wird z.B. Ihr Auftrag 5 auf den Nachmittag verschoben und auf die Prognosezeit verkürzt.
# Es ist eine Nachoptimierung, da jedes bereits eingeplante BEV seine
# prognostizierte Energie behalten darf und zulässig nach hinten geschoben wird
from collections import OrderedDict

from distributionAlgorithmForecastPolling import get_fair_share_charging_energy


def set_charging_start_if_fair_share_charging_energy_reached(simulation_day, simulation_data, minute_interval):
    for id_bev in get_sorted_descending_bev_id_with_parking_end_dict(simulation_day):
        fair_share_charging_energy = get_fair_share_charging_energy(simulation_day, id_bev, simulation_data,
                                                                    minute_interval)
        # Minuten Intervalle rückwärts von Parking end ablaufen und schauen wann fair_share_charging_energy erreicht
        # wenn erreicht dann setzte charging start



def sort_waiting_list_descending_by_parking_end(simulation_day):
    sorted_descending_bev_id_with_parking_end_dict = get_sorted_descending_bev_id_with_parking_end_dict(simulation_day)
    for id_bev in sorted_descending_bev_id_with_parking_end_dict.keys():
        simulation_day.waiting_bevs_list.add_bev(id_bev)


def get_sorted_descending_bev_id_with_parking_end_dict(simulation_day):
    bev_id_with_parking_end_dict = {}
    for id_bev in simulation_day.bevs_dict.get_bevs_dict().keys():
        parking_end = simulation_day.bevs_dict.get_parking_end_in_minutes(id_bev)
        if parking_end > 960:
            bev_id_with_parking_end_dict[id_bev] = 960
        bev_id_with_parking_end_dict[id_bev] = parking_end
    sorted_parking_end_list = sorted(bev_id_with_parking_end_dict.items(), key=lambda kv: kv[1])
    sorted_parking_end_list.reverse()
    sorted_descending_bev_id_with_parking_end_dict = OrderedDict(sorted_parking_end_list)
    print(sorted_descending_bev_id_with_parking_end_dict)
    return sorted_descending_bev_id_with_parking_end_dict
