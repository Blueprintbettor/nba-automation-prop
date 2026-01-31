# NBA PRA Automation (Cloud Run Ready)

Automated NBA prop analysis tool that pulls player props from Google Sheets, fetches PRA (Points + Rebounds + Assists) stats from the BallDontLie API, evaluates each prop, and sends formatted recommendations to Discord.

## 🎯 What This Does

1. **Pulls NBA prop lines** from Google Sheets (`INPUT_LINES` tab)
2. **Fetches player stats** from BallDontLie API (last 5 games)
3. **Evaluates each prop** based on averages and calculates edge
4. **Formats results** into a professional Discord slip
5. **Sends to Discord** via webhook
6. **Runs on Google Cloud Run** (serverless, scalable)

## 🏗️ Project Structure

```
nba-automation-prop/
├── main.py              # Flask app with /run endpoint
├── bdl_api.py          # BallDontLie API integration
├── pra_evaluator.py    # Prop evaluation logic
├── slip_builder.py     # Discord message formatting
├── requirements.txt    # Python dependencies
├── Dockerfile          # Cloud Run container config
├── .env               # Environment variables (local only)
├── DEPLOYMENT.md      # Cloud Run deployment guide
└── README.md          # This file
```

## 🚀 Quick Start

### Option 1: Deploy to Cloud Run (Recommended)

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete Cloud Run deployment instructions.

**TL;DR:**
```bash
gcloud run deploy nba-props-analyzer \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars SHEET_ID="your-sheet-id" \
    --set-env-vars DISCORD_WEBHOOK_URL="your-webhook"
```

### Option 2: Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/Blueprintbettor/nba-automation-prop.git
cd nba-automation-prop

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export SHEET_ID="your-google-sheet-id"
export DISCORD_WEBHOOK_URL="your-discord-webhook-url"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"

# 4. Run the app
python main.py

# 5. Trigger analysis (in another terminal)
curl -X POST http://localhost:8080/run
```

## 📊 Google Sheet Format

Your Google Sheet should have an `INPUT_LINES` tab with this structure:

| Date | Player | Stat | Line | Notes |
|------|--------|------|------|-------|
| 1/30/26 | LeBron James | PRA Over | 35.5 | vs Warriors |
| 1/30/26 | Stephen Curry | PRA Under | 40.5 | vs Lakers |
| 1/30/26 | Giannis Antetokounmpo | PRA Over | 45.5 | vs Nets |

**Column Details:**
- **Date**: Game date
- **Player**: Full player name
- **Stat**: Type of prop (e.g., "PRA Over", "PRA Under")
- **Line**: Betting line (numeric value)
- **Notes**: Optional notes

## 🎨 Discord Output Formats

The app supports two Discord formats:

### Default Format (Professional)
```
═══════════════════════════════════════
    🏀 NBA PROPS ANALYZER 🏀
    Thursday, January 30, 2026
═══════════════════════════════════════

📊 STRONG PLAYS

1. LeBron James
   Prop:       PRA Over 35.5
   L5 Avg PRA: 38.2
   Edge:       +2.7
   Confidence: MEDIUM

📈 SUMMARY
Total Props:    3
Strong Plays:   1
Leans:          1
Avoid:          1
```

### Simple Format
Set `USE_SIMPLE_FORMAT=true` environment variable:
```
🏀 NBA Props - January 30, 2026

1. LeBron James - PRA Over 35.5
   L5 Avg: 38.2 | Edge: +2.7 ✅

Total plays: 1
```

## 🧮 Evaluation Logic

The app evaluates props based on:

1. **Edge Calculation**: `Average PRA - Line`
2. **Confidence Levels**:
   - **HIGH**: Edge ≥ 5.0 points
   - **MEDIUM**: Edge ≥ 2.0 points
   - **LOW**: Edge < 2.0 points
3. **Recommendations**:
   - ✅ **PLAY**: Hit + High/Medium confidence
   - ⚠️ **LEAN**: Hit + Low confidence
   - ❌ **AVOID**: Miss

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SHEET_ID` | Google Sheet ID | Yes | - |
| `SHEET_RANGE` | Sheet range to read | No | `INPUT_LINES!A2:E50` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | Yes | - |
| `USE_SIMPLE_FORMAT` | Use simple Discord format | No | `false` |
| `PORT` | Server port | No | `8080` |

### Getting Your Google Sheet ID

Your Sheet ID is in the URL:
```
https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit
```

### Creating a Discord Webhook

1. Go to your Discord server
2. Server Settings → Integrations → Webhooks
3. Create webhook, copy URL
4. Use in `DISCORD_WEBHOOK_URL`

## 📡 API Endpoints

### `GET /`
Health check endpoint
```bash
curl https://your-service.run.app/
```
Returns: `{"status": "healthy", "service": "NBA Props Analyzer"}`

### `POST /run` or `GET /run`
Trigger prop analysis
```bash
curl -X POST https://your-service.run.app/run
```
Returns:
```json
{
  "ok": true,
  "props_count": 3,
  "summary": {
    "total": 3,
    "plays": 1,
    "leans": 1,
    "avoid": 1,
    "skip": 0
  },
  "message": "Successfully posted to Discord"
}
```

## 🤖 Automated Scheduling

Set up Cloud Scheduler to run automatically:

```bash
# Run daily at 9 AM Central Time
gcloud scheduler jobs create http nba-props-daily \
    --location us-central1 \
    --schedule "0 9 * * *" \
    --uri "https://your-service.run.app/run" \
    --http-method POST \
    --time-zone "America/Chicago"
```

## 📦 Dependencies

- **Flask**: Web framework
- **requests**: HTTP client
- **google-auth**: Google authentication
- **google-api-python-client**: Google Sheets API
- **gunicorn**: WSGI server for production

## 🐛 Troubleshooting

### "Permission denied" accessing Google Sheets
- Share your sheet with the service account email
- Service account needs "Viewer" permission

### BallDontLie API returns no data
- Check player name spelling (must match exactly)
- API is case-sensitive
- Free tier has rate limits

### Discord webhook fails
- Verify webhook URL is correct
- Check Discord channel permissions
- Test webhook manually with curl

## 📝 License

MIT License - feel free to use and modify

## 🤝 Contributing

Pull requests welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a PR

## 📞 Support

- Issues: [GitHub Issues](https://github.com/Blueprintbettor/nba-automation-prop/issues)
- Documentation: This README + DEPLOYMENT.md

---

**Built with ❤️ by Blueprint Bettor**
