import os
import requests
from flask import Flask, jsonify
from google.auth import default
from googleapiclient.discovery import build
from datetime import datetime
from bdl_api import get_last_5_avg_pra

app = Flask(__name__)

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")
SHEET_ID = os.environ.get("SHEET_ID")
SHEET_RANGE = os.environ.get("SHEET_RANGE", "INPUT_LINES!A2:E50")

def get_sheets_service():
    credentials, _ = default(scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
    return build('sheets', 'v4', credentials=credentials)

def read_sheet_data():
    service = get_sheets_service()
    result = service.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=SHEET_RANGE).execute()
    values = result.get('values', [])
    props = []
    for row in values:
        if len(row) < 2:
            continue
        prop = {
            'date': row[0] if len(row) > 0 else '',
            'player': row[1] if len(row) > 1 else '',
            'stat': row[2] if len(row) > 2 else '',
            'line': row[3] if len(row) > 3 else '',
            'notes': row[4] if len(row) > 4 else ''
        }
        props.append(prop)
    return props

def format_discord_message(props):
    if not props:
        return "NBA Props - No plays found"
    today = datetime.now().strftime("%B %d, %Y")
    lines = [f"**NBA Props - {today}**", ""]
    for i, prop in enumerate(props, 1):
        avg_pra = get_last_5_avg_pra(prop['player']) or 'N/A'
        lines.append(f"**{i}. {prop['player']}**")
        lines.append(f"   Stat: {prop['stat']}")
        lines.append(f"   Line: {prop['line']}")
        lines.append(f"   Avg PRA (Last 5): {avg_pra}")
        lines.append("")
    lines.append(f"_Total plays: {len(props)}_")
    return "\n".join(lines)

def post_to_discord(message):
    for _ in range(3):
        resp = requests.post(DISCORD_WEBHOOK, json={"content": message}, timeout=10)
        if resp.status_code in [200, 204]:
            return True
    return False

@app.route("/")
def health():
    return "OK", 200

@app.route("/run", methods=["POST", "GET"])
def run_nba_props():
    if not DISCORD_WEBHOOK or not SHEET_ID:
        return jsonify({"ok": False, "error": "Missing config"}), 500
    try:
        props = read_sheet_data()
        message = format_discord_message(props)
        post_to_discord(message)
        return jsonify({"ok": True, "props_count": len(props)}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
