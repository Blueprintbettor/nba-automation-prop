"""
Discord Slip Builder
Formats NBA props analysis for Discord messages
"""
from datetime import datetime
from typing import List, Dict


def build_discord_message(evaluated_props: List[Dict], summary: Dict) -> str:
    """
    Build professional Discord message with evaluated props
    
    Args:
        evaluated_props: List of evaluated props
        summary: Summary statistics dictionary
    
    Returns:
        Formatted Discord message string
    """
    if not evaluated_props:
        return "🏀 **NBA Props Analysis** - No props found today"
    
    today = datetime.now().strftime("%A, %B %d, %Y")
    
    lines = [
        "```",
        "═══════════════════════════════════════════",
        "         🏀 NBA PROPS ANALYZER 🏀",
        f"         {today}",
        "═══════════════════════════════════════════",
        "```",
        ""
    ]
    
    # Filter props by category
    plays = [p for p in evaluated_props if "✅ PLAY" in p.get("evaluation", {}).get("recommendation", "")]
    leans = [p for p in evaluated_props if "⚠️ LEAN" in p.get("evaluation", {}).get("recommendation", "")]
    
    # Strong Plays Section
    if plays:
        lines.append("**📊 STRONG PLAYS**")
        lines.append("```")
        for i, prop in enumerate(plays, 1):
            lines.extend(_format_prop(i, prop))
        lines.append("```")
        lines.append("")
    
    # Lean Plays Section
    if leans:
        lines.append("**⚠️ LEAN PLAYS** (Lower Confidence)")
        lines.append("```")
        for i, prop in enumerate(leans, 1):
            lines.extend(_format_prop(i, prop))
        lines.append("```")
        lines.append("")
    
    # No plays message
    if not plays and not leans:
        lines.append("_No strong plays identified today. Check back later!_")
        lines.append("")
    
    # Summary Section
    lines.append("**📈 SUMMARY**")
    lines.append("```")
    lines.append(f"Total Props Analyzed: {summary['total']}")
    lines.append(f"Strong Plays:         {summary['plays']}")
    lines.append(f"Leans:                {summary['leans']}")
    lines.append(f"Avoid:                {summary['avoids']}")
    if summary['skips'] > 0:
        lines.append(f"Skipped (No Data):    {summary['skips']}")
    lines.append("```")
    
    # Footer
    lines.append("")
    lines.append("_Powered by Blueprint Bettor | Data: BallDontLie API_")
    
    return "\n".join(lines)


def _format_prop(index: int, prop: Dict) -> List[str]:
    """
    Format a single prop for display
    
    Args:
        index: Prop number
        prop: Prop dictionary
    
    Returns:
        List of formatted lines
    """
    player = prop.get("player", "Unknown")
    stat = prop.get("stat", "PRA")
    line = prop.get("line", "N/A")
    avg_pra = prop.get("avg_pra", "N/A")
    edge = prop.get("evaluation", {}).get("edge", 0)
    confidence = prop.get("evaluation", {}).get("confidence", "N/A")
    
    lines = [
        f"{index}. {player}",
        f"   Prop:       {stat} {line}",
        f"   Avg (L5):   {avg_pra}",
        f"   Edge:       {edge:+.1f}",
        f"   Confidence: {confidence}",
        ""
    ]
    
    return lines


def build_simple_message(evaluated_props: List[Dict]) -> str:
    """
    Build simplified Discord message (compact format)
    
    Args:
        evaluated_props: List of evaluated props
    
    Returns:
        Formatted Discord message string
    """
    today = datetime.now().strftime("%B %d, %Y")
    
    # Filter to plays only
    plays = [p for p in evaluated_props if "✅ PLAY" in p.get("evaluation", {}).get("recommendation", "")]
    
    if not plays:
        return f"🏀 **NBA Props - {today}**\n\n_No strong plays identified today._"
    
    lines = [
        f"🏀 **NBA Props - {today}**",
        ""
    ]
    
    for i, prop in enumerate(plays, 1):
        player = prop.get("player", "Unknown")
        stat = prop.get("stat", "PRA")
        line = prop.get("line", "N/A")
        avg_pra = prop.get("avg_pra", "N/A")
        edge = prop.get("evaluation", {}).get("edge", 0)
        
        lines.append(f"**{i}. {player}** - {stat} {line}")
        lines.append(f"   L5 Avg: {avg_pra} | Edge: {edge:+.1f} ✅")
        lines.append("")
    
    lines.append(f"_Total plays: {len(plays)}_")
    
    return "\n".join(lines)
