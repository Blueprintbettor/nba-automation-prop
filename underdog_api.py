"""
Underdog Fantasy API Integration
Fetches real-time NBA injury data
"""
import requests
from typing import List, Dict, Optional

UNDERDOG_INJURIES_URL = "https://api.underdogfantasy.com/v2/nba/injuries"
REQUEST_TIMEOUT = 10


def get_injury_data() -> List[Dict]:
    """Fetch current NBA injury data from Underdog"""
    try:
        response = requests.get(UNDERDOG_INJURIES_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        return data.get("injuries", [])
    except Exception as e:
        print(f"Error fetching injury data: {e}")
        return []


def is_player_injured(player_name: str, injuries: List[Dict]) -> Optional[str]:
    """
    Check if a player is injured and return status
    Returns: "OUT", "DOUBTFUL", "QUESTIONABLE", or None
    """
    player_name_lower = player_name.lower()
    
    for injury in injuries:
        injured_player = injury.get("player_name", "").lower()
        
        if player_name_lower in injured_player or injured_player in player_name_lower:
            status = injury.get("status", "").upper()
            return status
    
    return None


def get_team_injuries(team_name: str, injuries: List[Dict]) -> List[Dict]:
    """Get all injuries for a specific team"""
    team_name_lower = team_name.lower()
    team_injuries = []
    
    for injury in injuries:
        injury_team = injury.get("team", "").lower()
        if team_name_lower in injury_team or injury_team in team_name_lower:
            team_injuries.append(injury)
    
    return team_injuries


def check_key_teammate_out(player_name: str, team_name: str, injuries: List[Dict]) -> bool:
    """
    Check if a key teammate is OUT (for usage bump logic)
    Key teammate = high usage player on same team
    """
    team_injuries = get_team_injuries(team_name, injuries)
    
    for injury in team_injuries:
        injured_player = injury.get("player_name", "")
        status = injury.get("status", "").upper()
        
        # Skip if it's the same player
        if injured_player.lower() in player_name.lower():
            continue
        
        # Check if OUT and appears to be a starter/key player
        if status == "OUT":
            # Simple heuristic: if they're listed, they're probably important
            return True
    
    return False
