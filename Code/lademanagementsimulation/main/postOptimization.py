# Nachoptimierungslauf:
# Aufträge nach Abfahrtzeit absteigend sortieren
# d.h. zuerst den Auftrag der als letzter das Parkhaus verlässt.
# Dann terminieren Sie diese rückwärts (d.h. Verfahren läuft spiegelverkehrt).
# Dadurch wird z.B. Ihr Auftrag 5 auf den Nachmittag verschoben und auf die Prognosezeit verkürzt.
# Es ist eine Nachoptimierung, da jedes bereits eingeplante BEV seine
# prognostizierte Energie behalten darf und zulässig nach hinten geschoben wird
from collections import OrderedDict


def sort_waiting_list_descending_by_parking_end(simulation_day):
    bev_id_with_parking_end_dict = {}
    for id_bev in simulation_day.bevs_dict.get_bevs_dict():
        # add to waiting list
        bev_id_with_parking_end_dict[id_bev] = simulation_day.bevs_dict.get_parking_end_in_minutes(id_bev)

    sorted_parking_end_list = sorted(bev_id_with_parking_end_dict.items(), key=lambda kv: kv[1])
    sorted_parking_end_list.reverse()
    sorted_descending_bev_id_with_parking_end_dict = OrderedDict(sorted_parking_end_list)
    print(sorted_descending_bev_id_with_parking_end_dict)

