"""
Game Context Engine
Calculates pace, defense ratings, and contextual factors
"""
from typing import Dict, List, Optional
from bdl_api import get_team_recent_games, get_box_score


def calculate_team_pace(team_id: int, num_games: int = 15) -> Optional[float]:
    """
    Calculate team pace (possessions per game) from recent games
    Pace formula: Possessions ≈ FGA + 0.4*FTA - ORB + TO
    """
    games = get_team_recent_games(team_id, num_games)
    
    if not games:
        return None
    
    total_possessions = 0
    valid_games = 0
    
    for game in games:
        game_id = game.get("id")
        if not game_id:
            continue
        
        # Get box score for possession calculation
        box_score = get_box_score(game_id)
        if not box_score:
            continue
        
        team_stats = _get_team_stats_from_box(box_score, team_id)
        if not team_stats:
            continue
        
        # Calculate possessions
        fga = team_stats.get("fga", 0)
        fta = team_stats.get("fta", 0)
        oreb = team_stats.get("oreb", 0)
        turnovers = team_stats.get("turnover", 0)
        
        possessions = fga + (0.4 * fta) - oreb + turnovers
        
        if possessions > 0:
            total_possessions += possessions
            valid_games += 1
    
    if valid_games == 0:
        return None
    
    avg_pace = total_possessions / valid_games
    return round(avg_pace, 1)


def calculate_team_defense(team_id: int, num_games: int = 15) -> Optional[float]:
    """
    Calculate opponent points per game (simpler defense metric)
    Lower = better defense
    """
    games = get_team_recent_games(team_id, num_games)
    
    if not games:
        return None
    
    total_opp_points = 0
    valid_games = 0
    
    for game in games:
        home_team_id = game.get("home_team", {}).get("id")
        away_team_id = game.get("visitor_team", {}).get("id")
        home_score = game.get("home_team_score", 0) or 0
        away_score = game.get("visitor_team_score", 0) or 0
        
        # Determine opponent score
        if team_id == home_team_id:
            opp_score = away_score
        elif team_id == away_team_id:
            opp_score = home_score
        else:
            continue
        
        if opp_score > 0:
            total_opp_points += opp_score
            valid_games += 1
    
    if valid_games == 0:
        return None
    
    avg_opp_points = total_opp_points / valid_games
    return round(avg_opp_points, 1)


def _get_team_stats_from_box(box_score: Dict, team_id: int) -> Optional[Dict]:
    """Extract aggregated team stats from box score"""
    stats_data = box_score.get("data", [])
    
    team_totals = {
        "fga": 0,
        "fta": 0,
        "oreb": 0,
        "turnover": 0
    }
    
    found_team = False
    
    for player_stat in stats_data:
        player_team_id = player_stat.get("team", {}).get("id")
        
        if player_team_id == team_id:
            found_team = True
            team_totals["fga"] += player_stat.get("fga", 0) or 0
            team_totals["fta"] += player_stat.get("fta", 0) or 0
            team_totals["oreb"] += player_stat.get("oreb", 0) or 0
            team_totals["turnover"] += player_stat.get("turnover", 0) or 0
    
    return team_totals if found_team else None


def get_matchup_context(player_name: str, opponent_team: Dict) -> Dict:
    """
    Get comprehensive matchup context
    Returns pace, defense rating, and contextual flags
    """
    opponent_id = opponent_team.get("id")
    opponent_name = opponent_team.get("full_name", "Unknown")
    
    if not opponent_id:
        return {
            "opponent_name": opponent_name,
            "pace": None,
            "defense_ppg": None,
            "context_flags": []
        }
    
    print(f"  Analyzing matchup vs {opponent_name}...")
    
    # Calculate opponent metrics
    pace = calculate_team_pace(opponent_id)
    defense_ppg = calculate_team_defense(opponent_id)
    
    context_flags = []
    
    # Pace context (simple thresholds)
    if pace:
        if pace >= 102:
            context_flags.append("Fast pace")
        elif pace <= 95:
            context_flags.append("Slow pace")
    
    # Defense context
    if defense_ppg:
        if defense_ppg <= 108:
            context_flags.append("Strong defense")
        elif defense_ppg >= 115:
            context_flags.append("Weak defense")
    
    return {
        "opponent_name": opponent_name,
        "opponent_id": opponent_id,
        "pace": pace,
        "defense_ppg": defense_ppg,
        "context_flags": context_flags
    }


def get_league_pace_rankings() -> Dict[str, float]:
    """
    Get simplified pace rankings (top/bottom thresholds)
    In production, this would query all teams
    """
    return {
        "top_5_threshold": 102,
        "bottom_5_threshold": 95
    }


def get_league_defense_rankings() -> Dict[str, float]:
    """
    Get simplified defense rankings (top/bottom thresholds)
    In production, this would query all teams
    """
    return {
        "top_5_threshold": 108,  # PPG allowed
        "bottom_5_threshold": 115
    }
