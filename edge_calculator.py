"""
Edge Calculator
Determines if props have meaningful edges
"""
from typing import Dict, List, Optional


def calculate_edge(projection: Dict) -> Optional[Dict]:
    """
    Calculate edge for a projection
    
    Returns:
        {
            "edge": float,
            "edge_type": "OVER" | "UNDER" | "NONE",
            "edge_strength": "STRONG" | "MODERATE" | "WEAK",
            "has_edge": bool
        }
    """
    projected_value = projection.get("projection")
    line = projection.get("line")
    
    if projected_value is None or line is None:
        return None
    
    try:
        line_float = float(line)
    except (ValueError, TypeError):
        return None
    
    # Calculate raw edge
    raw_edge = projected_value - line_float
    
    # Determine if it's an over or under edge
    edge_type = "NONE"
    edge_strength = "NONE"
    has_edge = False
    
    # Over edge logic
    if raw_edge >= 2.5:
        edge_type = "OVER"
        has_edge = True
        
        if raw_edge >= 5.0:
            edge_strength = "STRONG"
        elif raw_edge >= 3.5:
            edge_strength = "MODERATE"
        else:
            edge_strength = "WEAK"
    
    # Under edge logic
    elif raw_edge <= -2.5:
        edge_type = "UNDER"
        has_edge = True
        
        if raw_edge <= -5.0:
            edge_strength = "STRONG"
        elif raw_edge <= -3.5:
            edge_strength = "MODERATE"
        else:
            edge_strength = "WEAK"
    
    return {
        "edge": round(raw_edge, 1),
        "edge_type": edge_type,
        "edge_strength": edge_strength,
        "has_edge": has_edge
    }


def filter_edges(projections: List[Dict], min_edge: float = 2.5) -> List[Dict]:
    """
    Filter projections to only those with meaningful edges
    
    Args:
        projections: List of projection dictionaries
        min_edge: Minimum edge threshold (default 2.5)
    
    Returns:
        List of projections with edges
    """
    edges = []
    
    for projection in projections:
        edge_data = calculate_edge(projection)
        
        if not edge_data or not edge_data["has_edge"]:
            continue
        
        # Add edge data to projection
        projection["edge_data"] = edge_data
        edges.append(projection)
    
    return edges


def rank_edges(edges: List[Dict]) -> List[Dict]:
    """
    Rank edges by strength and confidence
    Priority: STRONG edges > MODERATE edges > WEAK edges
    Secondary: HIGH confidence > MEDIUM > LOW
    """
    def edge_score(edge: Dict) -> tuple:
        edge_data = edge.get("edge_data", {})
        
        # Strength score
        strength = edge_data.get("edge_strength", "NONE")
        strength_score = {"STRONG": 3, "MODERATE": 2, "WEAK": 1}.get(strength, 0)
        
        # Confidence score
        confidence = edge.get("confidence", "LOW")
        confidence_score = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(confidence, 1)
        
        # Absolute edge value
        abs_edge = abs(edge_data.get("edge", 0))
        
        return (strength_score, confidence_score, abs_edge)
    
    return sorted(edges, key=edge_score, reverse=True)


def get_edge_summary(edges: List[Dict]) -> Dict:
    """Generate summary statistics for edges"""
    if not edges:
        return {
            "total_edges": 0,
            "strong_edges": 0,
            "moderate_edges": 0,
            "weak_edges": 0,
            "over_edges": 0,
            "under_edges": 0
        }
    
    strong = sum(1 for e in edges if e.get("edge_data", {}).get("edge_strength") == "STRONG")
    moderate = sum(1 for e in edges if e.get("edge_data", {}).get("edge_strength") == "MODERATE")
    weak = sum(1 for e in edges if e.get("edge_data", {}).get("edge_strength") == "WEAK")
    
    over = sum(1 for e in edges if e.get("edge_data", {}).get("edge_type") == "OVER")
    under = sum(1 for e in edges if e.get("edge_data", {}).get("edge_type") == "UNDER")
    
    return {
        "total_edges": len(edges),
        "strong_edges": strong,
        "moderate_edges": moderate,
        "weak_edges": weak,
        "over_edges": over,
        "under_edges": under
    }
