"""
PRA Prop Evaluator
Analyzes NBA props and provides recommendations
"""
from typing import Dict, List, Optional


def evaluate_prop(line: float, avg_pra: float, prop_type: str = "over") -> Dict:
    """
    Evaluate a single prop bet
    
    Args:
        line: Betting line value
        avg_pra: Player's average PRA
        prop_type: "over" or "under"
    
    Returns:
        Dictionary with evaluation results
    """
    if avg_pra is None or line is None:
        return {
            "result": "SKIP",
            "confidence": "N/A",
            "edge": 0,
            "recommendation": "⚠️ Insufficient data"
        }
    
    # Calculate edge (how much better/worse than line)
    edge = avg_pra - line
    
    # Determine if prop would hit
    if prop_type.lower() == "over":
        hits = avg_pra > line
        edge_direction = edge
    else:  # under
        hits = avg_pra < line
        edge_direction = -edge
    
    # Determine confidence based on edge magnitude
    abs_edge = abs(edge_direction)
    if abs_edge >= 5.0:
        confidence = "HIGH"
    elif abs_edge >= 2.0:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    # Generate recommendation
    if hits and confidence in ["HIGH", "MEDIUM"]:
        recommendation = f"✅ PLAY ({confidence})"
    elif hits and confidence == "LOW":
        recommendation = "⚠️ LEAN (Borderline)"
    else:
        recommendation = f"❌ AVOID (Projected {prop_type.upper()} miss)"
    
    return {
        "result": "HIT" if hits else "MISS",
        "confidence": confidence,
        "edge": round(edge, 1),
        "recommendation": recommendation
    }


def evaluate_all_props(props: List[Dict]) -> List[Dict]:
    """
    Evaluate a list of props
    
    Args:
        props: List of prop dictionaries with keys: player, stat, line, avg_pra
    
    Returns:
        List of props with evaluation results added
    """
    evaluated = []
    
    for prop in props:
        # Extract data
        line_str = str(prop.get("line", "")).strip()
        avg_pra = prop.get("avg_pra")
        stat = str(prop.get("stat", "")).lower()
        
        # Parse line as float
        try:
            line = float(line_str)
        except (ValueError, TypeError):
            line = None
        
        # Determine prop type (over/under)
        prop_type = "under" if "under" in stat else "over"
        
        # Evaluate
        if avg_pra and avg_pra != "N/A":
            evaluation = evaluate_prop(line, avg_pra, prop_type)
        else:
            evaluation = {
                "result": "SKIP",
                "confidence": "N/A",
                "edge": 0,
                "recommendation": "⚠️ No data available"
            }
        
        # Add evaluation to prop
        prop["evaluation"] = evaluation
        prop["prop_type"] = prop_type
        evaluated.append(prop)
    
    return evaluated


def get_summary_stats(evaluated_props: List[Dict]) -> Dict:
    """
    Generate summary statistics for evaluated props
    
    Args:
        evaluated_props: List of evaluated props
    
    Returns:
        Dictionary with summary stats
    """
    total = len(evaluated_props)
    plays = sum(1 for p in evaluated_props if "✅ PLAY" in p.get("evaluation", {}).get("recommendation", ""))
    leans = sum(1 for p in evaluated_props if "⚠️ LEAN" in p.get("evaluation", {}).get("recommendation", ""))
    avoids = sum(1 for p in evaluated_props if "❌ AVOID" in p.get("evaluation", {}).get("recommendation", ""))
    skips = sum(1 for p in evaluated_props if "SKIP" in p.get("evaluation", {}).get("result", ""))
    
    return {
        "total": total,
        "plays": plays,
        "leans": leans,
        "avoids": avoids,
        "skips": skips
    }


def filter_props_by_recommendation(evaluated_props: List[Dict], category: str) -> List[Dict]:
    """
    Filter props by recommendation category
    
    Args:
        evaluated_props: List of evaluated props
        category: "plays", "leans", "avoids", or "skips"
    
    Returns:
        Filtered list of props
    """
    filters = {
        "plays": lambda p: "✅ PLAY" in p.get("evaluation", {}).get("recommendation", ""),
        "leans": lambda p: "⚠️ LEAN" in p.get("evaluation", {}).get("recommendation", ""),
        "avoids": lambda p: "❌ AVOID" in p.get("evaluation", {}).get("recommendation", ""),
        "skips": lambda p: "SKIP" in p.get("evaluation", {}).get("result", "")
    }
    
    filter_func = filters.get(category.lower())
    if not filter_func:
        return []
    
    return [p for p in evaluated_props if filter_func(p)]
