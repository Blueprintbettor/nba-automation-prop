"""
Projection Engine
Generates smart projections with contextual adjustments
"""
from typing import Dict, Optional
from bdl_api import get_player_stats_summary, find_player_game_today
from game_context import get_matchup_context
from underdog_api import get_injury_data, is_player_injured, check_key_teammate_out


def generate_projection(player_name: str, stat: str, num_games: int = 5) -> Optional[Dict]:
    """
    Generate contextual projection for a player's stat
    
    Returns:
        {
            "player_name": str,
            "stat": str,
            "baseline": float,
            "projection": float,
            "adjustments": list,
            "context": dict,
            "confidence": str
        }
    """
    print(f"\n🔍 Generating projection for {player_name} - {stat}")
    
    # Step 1: Get player's recent performance
    player_stats = get_player_stats_summary(player_name, stat, num_games)
    if not player_stats:
        print(f"  ✗ No stats found for {player_name}")
        return None
    
    baseline = player_stats["average"]
    if baseline is None:
        print(f"  ✗ No baseline average for {stat}")
        return None
    
    print(f"  ✓ Baseline average: {baseline}")
    
    # Step 2: Find today's game
    game_info = find_player_game_today(player_name)
    if not game_info:
        print(f"  ⚠️ No game found today")
        return {
            "player_name": player_name,
            "stat": stat,
            "baseline": baseline,
            "projection": baseline,
            "adjustments": ["No game today"],
            "context": {},
            "confidence": "LOW",
            "no_game": True
        }
    
    opponent = game_info["opponent"]
    is_home = game_info["is_home"]
    
    print(f"  ✓ Playing vs {opponent.get('full_name')} ({'Home' if is_home else 'Away'})")
    
    # Step 3: Get matchup context
    matchup_context = get_matchup_context(player_name, opponent)
    
    # Step 4: Check injuries
    injuries = get_injury_data()
    player_status = is_player_injured(player_name, injuries)
    
    if player_status == "OUT":
        print(f"  ✗ Player is OUT")
        return None
    
    player_team = player_stats["player"].get("team", {})
    team_name = player_team.get("full_name", "")
    
    teammate_out = check_key_teammate_out(player_name, team_name, injuries)
    
    # Step 5: Apply adjustments
    projection = baseline
    adjustments = []
    
    # Pace adjustment
    pace = matchup_context.get("pace")
    if pace:
        if pace >= 102:  # Fast pace
            boost = baseline * 0.05
            projection += boost
            adjustments.append(f"+{boost:.1f} (Fast pace: {pace})")
        elif pace <= 95:  # Slow pace
            penalty = baseline * 0.05
            projection -= penalty
            adjustments.append(f"-{penalty:.1f} (Slow pace: {pace})")
    
    # Defense adjustment
    defense_ppg = matchup_context.get("defense_ppg")
    if defense_ppg:
        if defense_ppg >= 115:  # Weak defense
            boost = baseline * 0.05
            projection += boost
            adjustments.append(f"+{boost:.1f} (Weak defense: {defense_ppg} PPG)")
        elif defense_ppg <= 108:  # Strong defense
            penalty = baseline * 0.05
            projection -= penalty
            adjustments.append(f"-{penalty:.1f} (Strong defense: {defense_ppg} PPG)")
    
    # Teammate injury adjustment
    if teammate_out:
        boost = baseline * 0.07
        projection += boost
        adjustments.append(f"+{boost:.1f} (Key teammate OUT)")
    
    # Player injury concern
    if player_status in ["QUESTIONABLE", "DOUBTFUL"]:
        adjustments.append(f"⚠️ Player status: {player_status}")
    
    # Confidence based on data quality
    confidence = "MEDIUM"
    if player_stats["num_games"] >= 5 and pace and defense_ppg:
        confidence = "HIGH"
    elif player_stats["num_games"] < 3:
        confidence = "LOW"
    
    projection = round(projection, 1)
    
    print(f"  ✓ Final projection: {projection} (adjustments: {len(adjustments)})")
    
    return {
        "player_name": player_name,
        "stat": stat,
        "baseline": baseline,
        "projection": projection,
        "adjustments": adjustments,
        "context": matchup_context,
        "confidence": confidence,
        "is_home": is_home,
        "player_status": player_status,
        "no_game": False
    }


def batch_generate_projections(props: list) -> list:
    """Generate projections for multiple props"""
    projections = []
    
    for prop in props:
        player_name = prop.get("player")
        stat = prop.get("stat", "PTS")
        
        if not player_name:
            continue
        
        projection = generate_projection(player_name, stat)
        
        if projection:
            projection["line"] = prop.get("line")
            projection["date"] = prop.get("date")
            projection["notes"] = prop.get("notes")
            projections.append(projection)
    
    return projections
