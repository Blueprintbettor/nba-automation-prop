"""
NBA Props Automation - Main Application
Flask app for automated NBA prop analysis
"""
import os
import sys
import requests
from flask import Flask, jsonify, request
from google.auth import default
from googleapiclient.discovery import build
from datetime import datetime

# Import local modules
from bdl_api import get_player_pra_stats
from pra_evaluator import evaluate_all_props, get_summary_stats
from slip_builder import build_discord_message, build_simple_message

# Initialize Flask app
app = Flask(__name__)

# Environment variables
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
SHEET_ID = os.environ.get("SHEET_ID")
SHEET_RANGE = os.environ.get("SHEET_RANGE", "INPUT_LINES!A2:E50")
BALLDONTLIE_API_KEY = os.environ.get("BALLDONTLIE_API_KEY")
USE_SIMPLE_FORMAT = os.environ.get("USE_SIMPLE_FORMAT", "false").lower() == "true"


def validate_environment():
    """Validate required environment variables are set"""
    missing = []
    
    if not DISCORD_WEBHOOK_URL:
        missing.append("DISCORD_WEBHOOK_URL")
    if not SHEET_ID:
        missing.append("SHEET_ID")
    if not BALLDONTLIE_API_KEY:
        missing.append("BALLDONTLIE_API_KEY")
    
    if missing:
        return False, f"Missing required environment variables: {', '.join(missing)}"
    
    return True, "All environment variables configured"


def get_sheets_service():
    """
    Get authenticated Google Sheets service
    
    Returns:
        Google Sheets API service object
    """
    try:
        credentials, _ = default(scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
        return build('sheets', 'v4', credentials=credentials)
    except Exception as e:
        print(f"Error creating Sheets service: {e}")
        raise


def read_props_from_sheet():
    """
    Read prop data from Google Sheets
    
    Returns:
        List of prop dictionaries
    """
    try:
        service = get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=SHEET_RANGE
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            print("No data found in sheet")
            return []
        
        props = []
        for row in values:
            # Skip empty rows
            if len(row) < 2:
                continue
            
            prop = {
                'date': row[0] if len(row) > 0 else '',
                'player': row[1] if len(row) > 1 else '',
                'stat': row[2] if len(row) > 2 else '',
                'line': row[3] if len(row) > 3 else '',
                'notes': row[4] if len(row) > 4 else ''
            }
            
            # Only add if player name exists
            if prop['player'].strip():
                props.append(prop)
        
        print(f"Read {len(props)} props from sheet")
        return props
        
    except Exception as e:
        print(f"Error reading from Google Sheets: {e}")
        raise


def fetch_pra_data(props):
    """
    Fetch PRA data for all props using BallDontLie API
    
    Args:
        props: List of prop dictionaries
    
    Returns:
        Props list with avg_pra added
    """
    print(f"\nFetching PRA data for {len(props)} players...")
    
    for i, prop in enumerate(props, 1):
        player_name = prop['player']
        print(f"\n[{i}/{len(props)}] {player_name}")
        
        try:
            stats = get_player_pra_stats(player_name, num_games=5)
            
            if stats:
                prop['avg_pra'] = stats['avg_pra_last_n']
                prop['games_found'] = stats['num_games']
            else:
                prop['avg_pra'] = None
                prop['games_found'] = 0
                
        except Exception as e:
            print(f"  ✗ Error fetching data: {e}")
            prop['avg_pra'] = None
            prop['games_found'] = 0
    
    print(f"\nCompleted data fetch for {len(props)} players")
    return props


def send_to_discord(message):
    """
    Send message to Discord webhook
    
    Args:
        message: Message string to send
    
    Returns:
        Boolean indicating success
    """
    if not DISCORD_WEBHOOK_URL:
        print("No Discord webhook URL configured")
        return False
    
    # Discord has a 2000 character limit per message
    # Split if needed
    if len(message) > 2000:
        # Split at a reasonable point
        parts = _split_message(message, 2000)
        for part in parts:
            success = _post_to_webhook(part)
            if not success:
                return False
        return True
    else:
        return _post_to_webhook(message)


def _post_to_webhook(message):
    """Post single message to Discord webhook"""
    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json={"content": message},
            timeout=10
        )
        
        if response.status_code in [200, 204]:
            print("✓ Successfully posted to Discord")
            return True
        else:
            print(f"✗ Discord returned status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error posting to Discord: {e}")
        return False


def _split_message(message, max_length):
    """Split message into chunks under max_length"""
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


# =============================================================================
# Flask Routes
# =============================================================================

@app.route("/")
def health_check():
    """Health check endpoint"""
    valid, message = validate_environment()
    
    return jsonify({
        "status": "healthy" if valid else "warning",
        "service": "NBA Props Analyzer",
        "version": "2.0",
        "environment_status": message,
        "timestamp": datetime.now().isoformat()
    }), 200 if valid else 500


@app.route("/run", methods=["GET", "POST"])
def run_analysis():
    """
    Main endpoint to run prop analysis
    
    Returns:
        JSON response with results
    """
    print("\n" + "="*60)
    print("NBA PROPS ANALYSIS - STARTING")
    print("="*60)
    
    # Validate environment
    valid, message = validate_environment()
    if not valid:
        print(f"✗ Environment validation failed: {message}")
        return jsonify({
            "ok": False,
            "error": message
        }), 500
    
    try:
        # Step 1: Read props from Google Sheets
        print("\n[1/5] Reading props from Google Sheets...")
        props = read_props_from_sheet()
        
        if not props:
            message = "🏀 **NBA Props** - No props found in sheet today"
            send_to_discord(message)
            return jsonify({
                "ok": True,
                "props_count": 0,
                "message": "No props found in sheet"
            }), 200
        
        # Step 2: Fetch PRA data from BallDontLie API
        print(f"\n[2/5] Fetching PRA data from BallDontLie API...")
        props_with_data = fetch_pra_data(props)
        
        # Step 3: Evaluate all props
        print(f"\n[3/5] Evaluating props...")
        evaluated_props = evaluate_all_props(props_with_data)
        summary = get_summary_stats(evaluated_props)
        
        print(f"\nEvaluation Summary:")
        print(f"  Total: {summary['total']}")
        print(f"  Plays: {summary['plays']}")
        print(f"  Leans: {summary['leans']}")
        print(f"  Avoid: {summary['avoids']}")
        print(f"  Skips: {summary['skips']}")
        
        # Step 4: Build Discord message
        print(f"\n[4/5] Building Discord message...")
        if USE_SIMPLE_FORMAT:
            message = build_simple_message(evaluated_props)
        else:
            message = build_discord_message(evaluated_props, summary)
        
        # Step 5: Send to Discord
        print(f"\n[5/5] Sending to Discord...")
        success = send_to_discord(message)
        
        print("\n" + "="*60)
        if success:
            print("✓ ANALYSIS COMPLETE - Posted to Discord")
        else:
            print("✗ ANALYSIS COMPLETE - Failed to post to Discord")
        print("="*60 + "\n")
        
        return jsonify({
            "ok": True,
            "props_count": len(props),
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


# =============================================================================
# Application Entry Point
# =============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"\n{'='*60}")
    print(f"NBA Props Analyzer v2.0")
    print(f"Starting on port {port}")
    print(f"{'='*60}\n")
    
    # Validate environment on startup
    valid, message = validate_environment()
    print(f"Environment: {message}\n")
    
    if not valid:
        print("⚠️  Warning: Missing required environment variables")
        print("The application may not function correctly.\n")
    
    app.run(host="0.0.0.0", port=port, debug=False)
