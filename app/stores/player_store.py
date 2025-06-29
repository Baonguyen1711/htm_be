from collections import defaultdict

player_info_dict = defaultdict(list)

def add_player_info(room_id: str, player_info: any):
    player_info_dict[f"{room_id}"].append(player_info)
    return player_info_dict[f"{room_id}"]

def get_player_info(room_id: str):
    return player_info_dict.get(f"{room_id}", [])
