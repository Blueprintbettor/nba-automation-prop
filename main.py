"""
NBA Props Edge Analyzer - Main Application
Production-ready Flask app with advanced prop evaluation
"""
import os
import requests
from flask import Flask, jsonify
from google.auth import default
from googleapiclient.discovery import build
from datetime import datetime

# Import modules
from projection_engine import batch_generate_projections
from edge_calculator import filter_edges, rank_edges, get_edge_summary
from discord_formatter import format_full_report, format_simple_report

# Initialize Flask
app = Flask(__name__)

# Environment variables
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
SHEET_ID = os.environ.get("SHEET_ID")
SHEET_RANGE = os.environ.get("SHEET_RANGE", "INPUT_LINES!A2:E50")
BALLDONTLIE_API_KEY = os.environ.get("BALLDONTLIE_API_KEY")
USE_SIMPLE_FORMAT = os.environ.get("USE_SIMPLE_FORMAT", "false").lower() == "true"


def validate_environment():
    """Validate required environment variables"""
    missing = []
    
    if not DISCORD_WEBHOOK_URL:
        missing.append("DISCORD_WEBHOOK_URL")
    if not SHEET_ID:
        missing.append("SHEET_ID")
    if not BALLDONTLIE_API_KEY:
        missing.append("BALLDONTLIE_API_KEY")
    
    if missing:
        return False, f"Missing: {', '.join(missing)}"
    
    return True, "Environment OK"


def get_sheets_service():
    """Get authenticated Google Sheets service"""
    try:
        credentials, _ = default(scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
        return build('sheets', 'v4', credentials=credentials)
    except Exception as e:
        print(f"Error creating Sheets service: {e}")
        raise


def read_props_from_sheet():
    """Read props from Google Sheets"""
    try:
        service = get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=SHEET_RANGE
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            print("No data in sheet")
            return []
        
        props = []
        for row in values:
            if len(row) < 4:  # Need at least Date, Player, Stat, Line
                continue
            
            prop = {
                'date': row[0] if len(row) > 0 else '',
                'player': row[1] if len(row) > 1 else '',
                'stat': row[2] if len(row) > 2 else '',
                'line': row[3] if len(row) > 3 else '',
                'notes': row[4] if len(row) > 4 else ''
            }
            
            if prop['player'].strip() and prop['line'].strip():
                props.append(prop)
        
        print(f"✓ Read {len(props)} props from sheet")
        return props
        
    except Exception as e:
        print(f"Error reading sheet: {e}")
        raise


def send_to_discord(message):
    """Send message to Discord webhook"""
    if not DISCORD_WEBHOOK_URL:
        print("No Discord webhook configured")
        return False
    
    # Split if too long (2000 char limit)
    if len(message) > 2000:
        parts = _split_message(message, 2000)
        for part in parts:
            success = _post_to_webhook(part)
            if not success:
                return False
        return True
    else:
        return _post_to_webhook(message)


def _post_to_webhook(message):
    """Post single message to Discord"""
    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json={"content": message},
            timeout=10
        )
        
        if response.status_code in [200, 204]:
            print("✓ Posted to Discord")
            return True
        else:
            print(f"✗ Discord returned {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Discord error: {e}")
        return False


def _split_message(message, max_length):
    """Split message into chunks"""
    parts = []
    current = ""
    
    for line in message.split("\n"):
        if len(current) + len(line) + 1 > max_length:
            parts.append(current)
            current = line + "\n"
        else:
            current += line + "\n"
    
    if current:
        parts.append(current)
    
    return parts


# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route("/")
def health_check():
    """Health check endpoint"""
    valid, message = validate_environment()
    
    return jsonify({
        "status": "healthy" if valid else "warning",
        "service": "NBA Props Edge Analyzer",
        "version": "2.0",
        "environment": message,
        "timestamp": datetime.now().isoformat()
    }), 200 if valid else 500


@app.route("/run", methods=["GET", "POST"])
def run_analysis():
    """
    Main endpoint - Run full edge analysis pipeline
    
    Pipeline:
    1. Read props from Google Sheets
    2. Generate contextual projections for each prop
    3. Calculate edges
    4. Filter and rank edges
    5. Format and post to Discord
    """
    print("\n" + "="*70)
    print("NBA PROPS EDGE ANALYZER - STARTING")
    print("="*70)
    
    # Validate environment
    valid, message = validate_environment()
    if not valid:
        print(f"✗ Environment error: {message}")
        return jsonify({"ok": False, "error": message}), 500
    
    try:
        # Step 1: Read props from sheet
        print("\n[1/6] Reading props from Google Sheets...")
        props = read_props_from_sheet()
        
        if not props:
            msg = "🏀 **NBA Props** - No props found in sheet today"
            send_to_discord(msg)
            return jsonify({
                "ok": True,
                "props_count": 0,
                "edges_found": 0,
                "message": "No props in sheet"
            }), 200
        
        print(f"      Found {len(props)} props")
        
        # Step 2: Generate projections
        print(f"\n[2/6] Generating contextual projections...")
        print(f"      (This may take 30-60 seconds for {len(props)} props)")
        projections = batch_generate_projections(props)
        
        print(f"      ✓ Generated {len(projections)} projections")
        
        if not projections:
            msg = "🏀 **NBA Props** - Could not generate projections (check player names)"
            send_to_discord(msg)
            return jsonify({
                "ok": True,
                "props_count": len(props),
                "edges_found": 0,
                "message": "No projections generated"
            }), 200
        
        # Step 3: Calculate edges
        print(f"\n[3/6] Calculating edges...")
        edges = filter_edges(projections, min_edge=2.5)
        
        print(f"      ✓ Found {len(edges)} edges")
        
        # Step 4: Rank edges
        print(f"\n[4/6] Ranking edges by strength...")
        ranked_edges = rank_edges(edges)
        summary = get_edge_summary(ranked_edges)
        
        print(f"      Strong: {summary['strong_edges']}")
        print(f"      Moderate: {summary['moderate_edges']}")
        print(f"      Weak: {summary['weak_edges']}")
        
        # Step 5: Format message
        print(f"\n[5/6] Formatting Discord message...")
        if USE_SIMPLE_FORMAT:
            message = format_simple_report(ranked_edges)
        else:
            message = format_full_report(ranked_edges, summary)
        
        # Step 6: Send to Discord
        print(f"\n[6/6] Sending to Discord...")
        success = send_to_discord(message)
        
        print("\n" + "="*70)
        if success:
            print(f"✓ COMPLETE - Posted {len(ranked_edges)} edges to Discord")
        else:
            print("✗ COMPLETE - Failed to post to Discord")
        print("="*70 + "\n")
        
        return jsonify({
            "ok": True,
            "props_count": len(props),
            "projections_generated": len(projections),
            "edges_found": len(ranked_edges),
            "summary": summary,
            "discord_posted": success,
            "message": "Analysis complete"
        }), 200
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    
    print(f"\n{'='*70}")
    print(f"NBA Props Edge Analyzer v2.0")
    print(f"Starting on port {port}")
    print(f"{'='*70}\n")
    
    valid, message = validate_environment()
    print(f"Environment: {message}\n")
    
    if not valid:
        print("⚠️  Warning: Missing environment variables")
        print("Application may not function correctly\n")
    
    app.run(host="0.0.0.0", port=port, debug=False)
