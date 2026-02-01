"""
BallDontLie API Integration - Enhanced
Comprehensive NBA data fetching with paid API key
"""
import os
import requests
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List

BASE_URL = "https://api.balldontlie.io"
API_KEY = os.environ.get("BALLDONTLIE_API_KEY")
MAX_RETRIES = 3
RETRY_DELAY = 2
REQUEST_TIMEOUT = 15


class BallDontLieAPIError(Exception):
    pass


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """Make authenticated request with retry logic"""
    if not API_KEY:
        raise BallDontLieAPIError("BALLDONTLIE_API_KEY not set")
    
    url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": API_KEY}
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, params=params or {}, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 429:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            raise BallDontLieAPIError(f"Request failed: {str(e)}")
    
    raise BallDontLieAPIError("Max retries exceeded")


def search_player(player_name: str) -> Optional[Dict]:
    """Search for player and return full player object"""
    try:
        data = _make_request("/v1/players", params={"search": player_name, "per_page": 5})
        players = data.get("data", [])
        return players[0] if players else None
    except Exception as e:
        print(f"Error searching for player '{player_name}': {e}")
        return None


def get_todays_games() -> List[Dict]:
    """Get all games scheduled for today"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        data = _make_request("/v1/games", params={
            "dates[]": today,
            "per_page": 100
        })
        return data.get("data", [])
    except Exception as e:
        print(f"Error fetching today's games: {e}")
        return []


def find_player_game_today(player_name: str) -> Optional[Dict]:
    """Find which game a player is playing today"""
    player = search_player(player_name)
    if not player:
        return None
    
    team_id = player.get("team", {}).get("id")
    if not team_id:
        return None
    
    todays_games = get_todays_games()
    
    for game in todays_games:
        home_team_id = game.get("home_team", {}).get("id")
        away_team_id = game.get("visitor_team", {}).get("id")
        
        if team_id == home_team_id:
            return {
                "game": game,
                "opponent": game.get("visitor_team"),
                "is_home": True
            }
        elif team_id == away_team_id:
            return {
                "game": game,
                "opponent": game.get("home_team"),
                "is_home": False
            }
    
    return None


def get_player_recent_games(player_id: int, num_games: int = 5) -> List[Dict]:
    """Get recent game stats for a player"""
    try:
        data = _make_request("/v1/stats", params={
            "player_ids[]": player_id,
            "per_page": num_games * 3,  # Fetch extra for DNPs
            "seasons[]": 2025
        })
        
        stats = data.get("data", [])
        
        # Filter to games where player actually played
        played_games = [
            game for game in stats 
            if game.get("min") and game["min"] != "0:00" and game.get("pts") is not None
        ]
        
        # Sort by date (most recent first) and take requested number
        played_games_sorted = sorted(
            played_games, 
            key=lambda x: x.get("game", {}).get("date", ""), 
            reverse=True
        )
        
        return played_games_sorted[:num_games]
        
    except Exception as e:
        print(f"Error getting recent games for player {player_id}: {e}")
        return []


def get_team_recent_games(team_id: int, num_games: int = 15) -> List[Dict]:
    """Get recent games for a team (for pace/defense calculations)"""
    try:
        # Get recent games
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Last 30 days
        
        data = _make_request("/v1/games", params={
            "team_ids[]": team_id,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "per_page": num_games
        })
        
        return data.get("data", [])
        
    except Exception as e:
        print(f"Error getting team games for team {team_id}: {e}")
        return []


def get_box_score(game_id: int) -> Optional[Dict]:
    """Get detailed box score for a game"""
    try:
        data = _make_request("/v1/stats", params={
            "game_ids[]": game_id,
            "per_page": 100
        })
        return data
    except Exception as e:
        print(f"Error getting box score for game {game_id}: {e}")
        return None


def calculate_stat_average(games: List[Dict], stat: str) -> Optional[float]:
    """Calculate average for a specific stat from game logs"""
    if not games:
        return None
    
    stat_lower = stat.lower()
    values = []
    
    for game in games:
        value = None
        
        # Map stat types
        if "pts" in stat_lower or "points" in stat_lower:
            value = game.get("pts", 0) or 0
        elif "reb" in stat_lower or "rebounds" in stat_lower:
            value = game.get("reb", 0) or 0
        elif "ast" in stat_lower or "assists" in stat_lower:
            value = game.get("ast", 0) or 0
        elif "pra" in stat_lower:
            pts = game.get("pts", 0) or 0
            reb = game.get("reb", 0) or 0
            ast = game.get("ast", 0) or 0
            value = pts + reb + ast
        elif "3" in stat_lower or "three" in stat_lower:
            value = game.get("fg3m", 0) or 0
        elif "stl" in stat_lower or "steals" in stat_lower:
            value = game.get("stl", 0) or 0
        elif "blk" in stat_lower or "blocks" in stat_lower:
            value = game.get("blk", 0) or 0
        elif "to" in stat_lower or "turnovers" in stat_lower:
            value = game.get("turnover", 0) or 0
        
        if value is not None:
            values.append(value)
    
    return round(sum(values) / len(values), 1) if values else None


def get_player_stats_summary(player_name: str, stat: str, num_games: int = 5) -> Optional[Dict]:
    """Get comprehensive player stats for a specific stat type"""
    player = search_player(player_name)
    if not player:
        return None
    
    player_id = player["id"]
    games = get_player_recent_games(player_id, num_games)
    
    if not games:
        return None
    
    avg = calculate_stat_average(games, stat)
    
    return {
        "player": player,
        "player_id": player_id,
        "stat": stat,
        "average": avg,
        "num_games": len(games),
        "recent_games": games
    }
