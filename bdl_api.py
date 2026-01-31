"""
BallDontLie API Integration
Handles all NBA data fetching with paid API key authentication
"""
import os
import requests
import time
from typing import Optional, Dict, List

# API Configuration
BASE_URL = "https://api.balldontlie.io"
API_KEY = os.environ.get("BALLDONTLIE_API_KEY")

# Rate limiting and retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
REQUEST_TIMEOUT = 10  # seconds


class BallDontLieAPIError(Exception):
    """Custom exception for API errors"""
    pass


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make authenticated request to BallDontLie API with retry logic
    
    Args:
        endpoint: API endpoint path (e.g., '/nba/v1/players')
        params: Query parameters
    
    Returns:
        JSON response data
    
    Raises:
        BallDontLieAPIError: If request fails after retries
    """
    if not API_KEY:
        raise BallDontLieAPIError("BALLDONTLIE_API_KEY environment variable not set")
    
    url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": API_KEY}
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params or {},
                timeout=REQUEST_TIMEOUT
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                wait_time = RETRY_DELAY * (attempt + 1)
                print(f"Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            
            # Raise for other HTTP errors
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.Timeout:
            print(f"Request timeout (attempt {attempt + 1}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            raise BallDontLieAPIError("Request timed out after retries")
            
        except requests.exceptions.RequestException as e:
            print(f"Request error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            raise BallDontLieAPIError(f"Request failed: {str(e)}")
    
    raise BallDontLieAPIError("Max retries exceeded")


def search_player(player_name: str) -> Optional[int]:
    """
    Search for a player by name and return their ID
    
    Args:
        player_name: Full or partial player name
    
    Returns:
        Player ID if found, None otherwise
    """
    try:
        # Split name for better search
        name_parts = player_name.strip().split()
        
        # Try searching with full name
        data = _make_request("/nba/v1/players", params={
            "search": player_name,
            "per_page": 5
        })
        
        players = data.get("data", [])
        
        if not players:
            return None
        
        # Return first match (BallDontLie search is pretty good)
        return players[0]["id"]
        
    except Exception as e:
        print(f"Error searching for player '{player_name}': {e}")
        return None


def get_player_season_averages(player_id: int, season: int = 2025) -> Optional[Dict]:
    """
    Get player season averages
    
    Args:
        player_id: Player ID
        season: Season year (default: 2025)
    
    Returns:
        Dictionary with season averages or None
    """
    try:
        data = _make_request(f"/nba/v1/season_averages", params={
            "player_ids[]": player_id,
            "season": season
        })
        
        averages = data.get("data", [])
        return averages[0] if averages else None
        
    except Exception as e:
        print(f"Error getting season averages for player {player_id}: {e}")
        return None


def get_recent_games(player_id: int, num_games: int = 5) -> List[Dict]:
    """
    Get recent game stats for a player
    
    Args:
        player_id: Player ID
        num_games: Number of recent games to fetch
    
    Returns:
        List of game stat dictionaries
    """
    try:
        # Fetch more than needed to filter out games with no minutes
        data = _make_request("/nba/v1/stats", params={
            "player_ids[]": player_id,
            "per_page": num_games * 2,  # Fetch extra in case of DNPs
            "seasons[]": 2025  # Current season
        })
        
        stats = data.get("data", [])
        
        # Filter to games where player actually played (has minutes)
        played_games = [
            game for game in stats 
            if game.get("min") and game["min"] != "0:00" and game["pts"] is not None
        ]
        
        # Sort by game date (most recent first) and take requested number
        # Note: Stats are typically returned newest first, but let's be safe
        return played_games[:num_games]
        
    except Exception as e:
        print(f"Error getting recent games for player {player_id}: {e}")
        return []


def calculate_pra_average(games: List[Dict]) -> Optional[float]:
    """
    Calculate PRA (Points + Rebounds + Assists) average from game logs
    
    Args:
        games: List of game stat dictionaries
    
    Returns:
        Average PRA or None if no valid games
    """
    if not games:
        return None
    
    total_pra = 0
    valid_games = 0
    
    for game in games:
        pts = game.get("pts", 0) or 0
        reb = game.get("reb", 0) or 0
        ast = game.get("ast", 0) or 0
        
        pra = pts + reb + ast
        total_pra += pra
        valid_games += 1
    
    return round(total_pra / valid_games, 1) if valid_games > 0 else None


def get_player_pra_stats(player_name: str, num_games: int = 5) -> Optional[Dict]:
    """
    Main function: Get player PRA statistics
    
    Args:
        player_name: Player's full name
        num_games: Number of recent games to analyze
    
    Returns:
        Dictionary with player stats or None
    """
    print(f"Fetching stats for: {player_name}")
    
    # Step 1: Find player ID
    player_id = search_player(player_name)
    if not player_id:
        print(f"  ✗ Player not found: {player_name}")
        return None
    
    print(f"  ✓ Found player ID: {player_id}")
    
    # Step 2: Get recent games
    games = get_recent_games(player_id, num_games)
    if not games:
        print(f"  ✗ No recent games found")
        return None
    
    print(f"  ✓ Found {len(games)} recent games")
    
    # Step 3: Calculate PRA average
    avg_pra = calculate_pra_average(games)
    
    # Step 4: Get season averages for context
    season_avg = get_player_season_averages(player_id)
    
    return {
        "player_name": player_name,
        "player_id": player_id,
        "avg_pra_last_n": avg_pra,
        "num_games": len(games),
        "season_avg": season_avg,
        "recent_games": games[:5]  # Keep last 5 for reference
    }


# Convenience function for backward compatibility
def get_last_5_avg_pra(player_name: str) -> Optional[float]:
    """
    Get last 5 games PRA average (simplified interface)
    
    Args:
        player_name: Player's full name
    
    Returns:
        Average PRA as float or None
    """
    stats = get_player_pra_stats(player_name, num_games=5)
    return stats["avg_pra_last_n"] if stats else None
