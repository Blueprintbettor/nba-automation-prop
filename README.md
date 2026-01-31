# NBA Props Automation v2.0

Production-ready NBA prop analysis system that pulls player props from Google Sheets, analyzes them using the BallDontLie API, and posts recommendations to Discord.

## 🎯 Features

- ✅ **Paid BallDontLie API Integration** - Fast, reliable NBA stats
- ✅ **Automated PRA Analysis** - Points + Rebounds + Assists evaluation
- ✅ **Smart Recommendations** - Play/Lean/Avoid with confidence levels
- ✅ **Professional Discord Formatting** - Clean, organized messages
- ✅ **Google Sheets Integration** - Easy prop input
- ✅ **Cloud Run Ready** - Serverless deployment
- ✅ **Error Handling** - Retry logic and graceful failures
- ✅ **Production Logging** - Full visibility into operations

## 📊 How It Works

```
Google Sheets (Props)
         ↓
BallDontLie API (Player Stats)
         ↓
PRA Evaluator (Analysis)
         ↓
Discord Slip Builder (Formatting)
         ↓
Discord Webhook (Post)
```

## 🚀 Quick Start

### Option 1: Deploy to Google Cloud Run (Recommended)

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete instructions.

**Quick Deploy:**
```bash
gcloud run deploy nba-props-analyzer \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars SHEET_ID="1BEWBO-JZWQIjAtIgL69sK47ZXnLPwkE4VYI_uVVq8bg" \
    --set-env-vars DISCORD_WEBHOOK_URL="your-webhook" \
    --set-env-vars BALLDONTLIE_API_KEY="your-api-key"
```

### Option 2: Run Locally

```bash
# 1. Clone repository
git clone <your-repo-url>
cd nba-props-automation

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your values

# 4. Run application
python main.py

# 5. Trigger analysis (in another terminal)
curl -X POST http://localhost:8080/run
```

## 🔧 Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | `https://discord.com/api/webhooks/...` |
| `SHEET_ID` | Google Sheets ID | `1BEWBO-JZWQIjAtIgL69sK47ZXnLPwkE4VYI_uVVq8bg` |
| `BALLDONTLIE_API_KEY` | BallDontLie API key | `ccd6b645-9f53-476d-a7a6-dc46b5159003` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SHEET_RANGE` | Google Sheets range | `INPUT_LINES!A2:E50` |
| `USE_SIMPLE_FORMAT` | Use simple Discord format | `false` |
| `PORT` | Server port | `8080` |

### Google Sheets Format

Your Google Sheet should have an `INPUT_LINES` tab with this structure:

| Date | Player | Stat | Line | Notes |
|------|--------|------|------|-------|
| 1/30/26 | LeBron James | PRA Over | 35.5 | vs GSW |
| 1/30/26 | Stephen Curry | PRA Under | 40.5 | vs LAL |

**Columns:**
- **Date**: Game date
- **Player**: Full player name (must match NBA records)
- **Stat**: Prop type (e.g., "PRA Over", "PRA Under")
- **Line**: Betting line (numeric)
- **Notes**: Optional notes

## 📡 API Endpoints

### `GET /`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "service": "NBA Props Analyzer",
  "version": "2.0",
  "environment_status": "All environment variables configured",
  "timestamp": "2026-01-30T12:00:00"
}
```

### `POST /run` or `GET /run`
Trigger prop analysis

**Response:**
```json
{
  "ok": true,
  "props_count": 5,
  "summary": {
    "total": 5,
    "plays": 2,
    "leans": 1,
    "avoids": 2,
    "skips": 0
  },
  "discord_posted": true,
  "message": "Analysis complete"
}
```

## 🎨 Discord Output

### Professional Format (Default)

```
═══════════════════════════════════════════
         🏀 NBA PROPS ANALYZER 🏀
         Thursday, January 30, 2026
═══════════════════════════════════════════

📊 STRONG PLAYS

1. LeBron James
   Prop:       PRA Over 35.5
   Avg (L5):   38.2
   Edge:       +2.7
   Confidence: MEDIUM

📈 SUMMARY
Total Props Analyzed: 5
Strong Plays:         2
Leans:                1
Avoid:                2
```

### Simple Format
Set `USE_SIMPLE_FORMAT=true`:

```
🏀 NBA Props - January 30, 2026

1. LeBron James - PRA Over 35.5
   L5 Avg: 38.2 | Edge: +2.7 ✅

Total plays: 2
```

## 🧮 Evaluation Logic

**Edge Calculation:**
- Edge = Average PRA - Line
- For "Under" props, edge is inverted

**Confidence Levels:**
- **HIGH**: Edge ≥ 5.0 points
- **MEDIUM**: Edge ≥ 2.0 points
- **LOW**: Edge < 2.0 points

**Recommendations:**
- ✅ **PLAY**: Projected hit with HIGH or MEDIUM confidence
- ⚠️ **LEAN**: Projected hit with LOW confidence
- ❌ **AVOID**: Projected miss
- ⚠️ **SKIP**: Insufficient data

## 📁 Project Structure

```
nba-props-automation/
├── main.py              # Flask application
├── bdl_api.py          # BallDontLie API integration
├── pra_evaluator.py    # Prop evaluation logic
├── slip_builder.py     # Discord message formatting
├── requirements.txt    # Python dependencies
├── Dockerfile          # Cloud Run configuration
├── .env.example        # Environment template
├── .gitignore         # Git ignore rules
├── .dockerignore      # Docker ignore rules
├── README.md          # This file
└── DEPLOYMENT.md      # Deployment guide
```

## 🔌 BallDontLie API Integration

This project uses the **paid BallDontLie API** for reliable, fast NBA data.

**Features:**
- Automatic retry logic with exponential backoff
- Rate limit handling
- Error resilience
- Player search by name
- Recent game stats (last 5 games)
- Season averages

**API Endpoints Used:**
- `/nba/v1/players` - Player search
- `/nba/v1/stats` - Game statistics
- `/nba/v1/season_averages` - Season averages

## 🛠️ Development

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export BALLDONTLIE_API_KEY="your-key"
export SHEET_ID="your-sheet-id"
export DISCORD_WEBHOOK_URL="your-webhook"

# Run locally
python main.py

# Test endpoint
curl -X POST http://localhost:8080/run
```

### Docker Testing

```bash
# Build image
docker build -t nba-props .

# Run container
docker run -p 8080:8080 \
    -e BALLDONTLIE_API_KEY="your-key" \
    -e SHEET_ID="your-sheet-id" \
    -e DISCORD_WEBHOOK_URL="your-webhook" \
    nba-props

# Test
curl -X POST http://localhost:8080/run
```

## 🐛 Troubleshooting

### "Player not found"
- Check player name spelling (must match NBA records exactly)
- Try full name: "LeBron James" not "Lebron"
- Check if player is currently active in the NBA

### "No recent games found"
- Player may not have played in last few games (injury/DNP)
- Check if it's during NBA season
- Verify player ID is correct

### "Rate limit exceeded"
- Paid API should have high limits
- Check your API key tier
- App automatically retries with backoff

### "Google Sheets permission denied"
- Share sheet with service account email
- Grant "Viewer" permission
- Check service account configuration

### "Discord webhook failed"
- Verify webhook URL is correct
- Check Discord channel permissions
- Test webhook: `curl -X POST <webhook-url> -d '{"content":"test"}'`

## 📈 Performance

- **Average analysis time**: 30-60 seconds for 10 props
- **API calls per prop**: 2-3 calls (player search + stats)
- **Memory usage**: ~100MB
- **Cloud Run cost**: ~$0-2/month with occasional use

## 🔐 Security Notes

- Never commit `.env` file to git
- Rotate API keys regularly
- Use Cloud Run secrets for production
- Share Google Sheets with service account only
- Keep Discord webhook URLs private

## 📝 License

MIT License - feel free to use and modify

## 🤝 Contributing

Issues and pull requests welcome!

## 📞 Support

- **Documentation**: See README.md and DEPLOYMENT.md
- **Issues**: Open a GitHub issue
- **BallDontLie API**: https://www.balldontlie.io/docs

---

**Built with ❤️ by Blueprint Bettor**

Powered by BallDontLie API | Deployed on Google Cloud Run
