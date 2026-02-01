"""
Discord Formatter
Creates rich, informative Discord messages for edges
"""
from datetime import datetime
from typing import List, Dict


def format_edge_message(edge: Dict) -> str:
    """
    Format a single edge into a Discord message block
    
    Example output:
    ✅ EDGE FOUND: Jayson Tatum
    ▪️ Stat: Points
    ▪️ Line: 27.5
    ▪️ Projection: 31.1
    ▪️ Edge: +3.6 (MODERATE OVER)
    ▪️ Opponent: Miami Heat
    ▪️ Context: Fast pace, Weak defense
    """
    player_name = edge.get("player_name", "Unknown")
    stat = edge.get("stat", "PTS")
    line = edge.get("line", "N/A")
    projection = edge.get("projection", 0)
    
    edge_data = edge.get("edge_data", {})
    edge_value = edge_data.get("edge", 0)
    edge_type = edge_data.get("edge_type", "NONE")
    edge_strength = edge_data.get("edge_strength", "WEAK")
    
    context = edge.get("context", {})
    opponent_name = context.get("opponent_name", "Unknown")
    context_flags = context.get("context_flags", [])
    
    adjustments = edge.get("adjustments", [])
    confidence = edge.get("confidence", "MEDIUM")
    is_home = edge.get("is_home", False)
    
    # Build message
    lines = []
    
    # Header
    icon = "✅" if edge_strength == "STRONG" else "⚠️" if edge_strength == "MODERATE" else "📊"
    lines.append(f"{icon} **EDGE FOUND: {player_name}**")
    
    # Core info
    lines.append(f"▪️ **Stat:** {stat}")
    lines.append(f"▪️ **Line:** {line}")
    lines.append(f"▪️ **Projection:** {projection}")
    
    # Edge details
    edge_sign = "+" if edge_value > 0 else ""
    lines.append(f"▪️ **Edge:** {edge_sign}{edge_value} ({edge_strength} {edge_type})")
    
    # Matchup info
    home_away = "@ Home" if is_home else "@ Away"
    lines.append(f"▪️ **Opponent:** {opponent_name} {home_away}")
    
    # Context
    if context_flags:
        context_str = ", ".join(context_flags)
        lines.append(f"▪️ **Context:** {context_str}")
    
    # Adjustments (if any notable ones)
    if adjustments:
        key_adjustments = [adj for adj in adjustments if not adj.startswith("⚠️")]
        if key_adjustments:
            adj_summary = " | ".join(key_adjustments[:2])  # Show top 2
            lines.append(f"▪️ **Factors:** {adj_summary}")
    
    # Confidence
    lines.append(f"▪️ **Confidence:** {confidence}")
    
    lines.append("")  # Blank line for separation
    
    return "\n".join(lines)


def format_full_report(edges: List[Dict], summary: Dict) -> str:
    """
    Format complete Discord report with all edges
    """
    today = datetime.now().strftime("%A, %B %d, %Y")
    
    lines = [
        "```",
        "═══════════════════════════════════════════",
        "      🏀 NBA PROPS EDGE ANALYZER 🏀",
        f"           {today}",
        "═══════════════════════════════════════════",
        "```",
        ""
    ]
    
    if not edges:
        lines.append("**No edges found today.** All props appear fairly priced.")
        lines.append("")
        lines.append("_Check back later for updated lines!_")
        return "\n".join(lines)
    
    # Group by strength
    strong_edges = [e for e in edges if e.get("edge_data", {}).get("edge_strength") == "STRONG"]
    moderate_edges = [e for e in edges if e.get("edge_data", {}).get("edge_strength") == "MODERATE"]
    weak_edges = [e for e in edges if e.get("edge_data", {}).get("edge_strength") == "WEAK"]
    
    # Strong edges section
    if strong_edges:
        lines.append("## 🔥 STRONG EDGES")
        lines.append("")
        for edge in strong_edges:
            lines.append(format_edge_message(edge))
    
    # Moderate edges section
    if moderate_edges:
        lines.append("## ⚡ MODERATE EDGES")
        lines.append("")
        for edge in moderate_edges:
            lines.append(format_edge_message(edge))
    
    # Weak edges (optional, only if not too many)
    if weak_edges and len(weak_edges) <= 3:
        lines.append("## 📈 BORDERLINE EDGES")
        lines.append("")
        for edge in weak_edges:
            lines.append(format_edge_message(edge))
    
    # Summary
    lines.append("```")
    lines.append("━━━━━━━━━━━━━━━━ SUMMARY ━━━━━━━━━━━━━━━━")
    lines.append(f"Total Edges:      {summary['total_edges']}")
    lines.append(f"Strong:           {summary['strong_edges']}")
    lines.append(f"Moderate:         {summary['moderate_edges']}")
    lines.append(f"Weak:             {summary['weak_edges']}")
    lines.append(f"Over Edges:       {summary['over_edges']}")
    lines.append(f"Under Edges:      {summary['under_edges']}")
    lines.append("```")
    
    # Footer
    lines.append("")
    lines.append("_Powered by Blueprint Bettor | Data: BallDontLie + Underdog_")
    lines.append("_Projections use pace, defense, injuries, and recent form_")
    
    return "\n".join(lines)


def format_simple_report(edges: List[Dict]) -> str:
    """Simplified format for quick scanning"""
    if not edges:
        return "🏀 **NBA Props** - No edges found today"
    
    today = datetime.now().strftime("%B %d, %Y")
    lines = [f"🏀 **NBA Props Edge Report - {today}**", ""]
    
    for i, edge in enumerate(edges, 1):
        player = edge.get("player_name")
        stat = edge.get("stat")
        line = edge.get("line")
        projection = edge.get("projection")
        edge_data = edge.get("edge_data", {})
        edge_val = edge_data.get("edge", 0)
        edge_type = edge_data.get("edge_type", "")
        
        lines.append(f"**{i}. {player}** - {stat} {line}")
        lines.append(f"   Proj: {projection} | Edge: {edge_val:+.1f} ({edge_type})")
        lines.append("")
    
    lines.append(f"_Found {len(edges)} edges_")
    
    return "\n".join(lines)
