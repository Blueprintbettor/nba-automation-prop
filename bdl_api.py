import requests

BASE_URL = "https://www.balldontlie.io/api/v1"

def get_player_id(name):
    resp = requests.get(f"{BASE_URL}/players", params={"search": name})
    data = resp.json()
    if data["data"]:
        return data["data"][0]["id"]
    return None

def get_last_5_game_stats(player_id):
    games = []
    page = 1
    while len(games) < 5:
        resp = requests.get(f"{BASE_URL}/stats", params={"player_ids[]": player_id, "per_page": 100, "page": page})
        data = resp.json().get("data", [])
        for game in data:
            if game["min"] and game["pts"] is not None:
                games.append(game)
                if len(games) == 5:
                    break
        page += 1
    return games

def calculate_avg_pra(game_logs):
    total_pra = 0
    for game in game_logs:
        pra = game["pts"] + game["reb"] + game["ast"]
        total_pra += pra
    return round(total_pra / len(game_logs), 1) if game_logs else 0

def get_last_5_avg_pra(player_name):
    player_id = get_player_id(player_name)
    if not player_id:
        return None
    logs = get_last_5_game_stats(player_id)
    return calculate_avg_pra(logs)
