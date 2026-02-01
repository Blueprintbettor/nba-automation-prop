# 🚀 NBA Props Analyzer v2.0 - Deployment Guide

Complete deployment instructions for the advanced edge detection system.

## ✨ What's New in v2.0

### Advanced Features
- ✅ **Real opponent detection** - Finds who each player faces today
- ✅ **Dynamic pace calculations** - From last 15 games (not static tables)
- ✅ **Defensive ratings** - Opponent points allowed per game
- ✅ **Injury integration** - Real-time Underdog Fantasy injury data
- ✅ **Contextual adjustments** - Pace, defense, teammate injuries
- ✅ **Smart edge detection** - Only posts props with 2.5+ edge
- ✅ **Ranked edges** - STRONG > MODERATE > WEAK

### Edge Calculation Logic
```
Projection = Baseline Average
  + 5% if opponent pace is fast (≥102)
  - 5% if opponent pace is slow (≤95)
  + 5% if opponent defense is weak (≥115 PPG)
  - 5% if opponent defense is strong (≤108 PPG)
  + 7% if key teammate is OUT

Edge = Projection - Line

IF edge ≥ +2.5 → OVER EDGE
IF edge ≤ -2.5 → UNDER EDGE
ELSE → Skip (no edge)
```

## 📋 Prerequisites

- Google Cloud account with billing enabled
- `gcloud` CLI installed
- Your environment variables:
  ```
  SHEET_ID=1BEWBO-JZWQIjAtIgL69sK47ZXnLPwkE4VYI_uVVq8bg
  DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
  BALLDONTLIE_API_KEY=ccd6b645-9f53-476d-a7a6-dc46b5159003
  ```

## 🎯 Quick Deploy (5 Minutes)

### Step 1: Upload to Cloud Shell

1. Upload the entire `nba-props-v2-complete` folder to Cloud Shell
2. Or clone from your GitHub repo

### Step 2: Navigate and Deploy

```bash
cd nba-props-v2-complete

gcloud run deploy nba-props-analyzer-v2 \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars SHEET_ID="1BEWBO-JZWQIjAtIgL69sK47ZXnLPwkE4VYI_uVVq8bg" \
    --set-env-vars DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/1456668428784894184/QQeq0pHtiZWZqHpiQ2pyRxIf3CyZ64sqAohB0RW_yu_9oiWg1fEntfrlz88fV13_JXkp" \
    --set-env-vars BALLDONTLIE_API_KEY="ccd6b645-9f53-476d-a7a6-dc46b5159003" \
    --timeout 180 \
    --memory 1Gi
```

**Note:** Increased timeout (180s) and memory (1Gi) for complex calculations.

### Step 3: Test

```bash
curl -X POST https://YOUR-SERVICE-URL/run
```

## 📊 Google Sheet Format

Your sheet (`INPUT_LINES` tab) should look like:

| Date | Player | Stat | Line | Notes |
|------|--------|------|------|-------|
| 2/1/26 | Jayson Tatum | PTS | 27.5 | vs MIA |
| 2/1/26 | LeBron James | PRA | 42.5 | vs GSW |
| 2/1/26 | Stephen Curry | AST | 6.5 | vs LAL |

**Supported Stats:**
- `PTS` or `Points` - Points
- `REB` or `Rebounds` - Rebounds
- `AST` or `Assists` - Assists
- `PRA` - Points + Rebounds + Assists
- `3PM` or `Threes` - Three pointers made
- `STL` or `Steals` - Steals
- `BLK` or `Blocks` - Blocks

## 🎨 Discord Output Example

```
═══════════════════════════════════════════
      🏀 NBA PROPS EDGE ANALYZER 🏀
           Friday, February 01, 2026
═══════════════════════════════════════════

## 🔥 STRONG EDGES

✅ EDGE FOUND: Jayson Tatum
▪️ Stat: PTS
▪️ Line: 27.5
▪️ Projection: 31.8
▪️ Edge: +4.3 (STRONG OVER)
▪️ Opponent: Miami Heat @ Home
▪️ Context: Fast pace, Weak defense
▪️ Factors: +1.3 (Fast pace: 104) | +1.4 (Weak defense: 116.2 PPG)
▪️ Confidence: HIGH

━━━━━━━━━━━━━━━━ SUMMARY ━━━━━━━━━━━━━━━━
Total Edges:      3
Strong:           1
Moderate:         1
Weak:             1
Over Edges:       2
Under Edges:      1
```

## 🔧 Advanced Configuration

### Adjust Edge Threshold

In `edge_calculator.py`, change line 48:

```python
# Current: 2.5 edge threshold
if raw_edge >= 2.5:
    
# Change to 3.0 for stricter edges:
if raw_edge >= 3.0:
```

### Adjust Contextual Boosts

In `projection_engine.py`, lines 75-107:

```python
# Current boosts
pace_boost = baseline * 0.05  # 5%
defense_boost = baseline * 0.05  # 5%
teammate_boost = baseline * 0.07  # 7%

# Make more aggressive:
pace_boost = baseline * 0.08  # 8%
```

### Use Simple Format

Set environment variable:
```bash
--set-env-vars USE_SIMPLE_FORMAT="true"
```

## 🔄 Automated Scheduling

### Daily at 9 AM

```bash
# Enable Cloud Scheduler
gcloud services enable cloudscheduler.googleapis.com

# Get service URL
SERVICE_URL=$(gcloud run services describe nba-props-analyzer-v2 \
    --region us-central1 \
    --format 'value(status.url)')

# Create daily job
gcloud scheduler jobs create http nba-props-daily-v2 \
    --location us-central1 \
    --schedule "0 9 * * *" \
    --uri "${SERVICE_URL}/run" \
    --http-method POST \
    --time-zone "America/Chicago" \
    --description "Daily NBA props edge analysis"
```

## 📊 Monitoring

### View Logs

```bash
gcloud run services logs read nba-props-analyzer-v2 \
    --region us-central1 \
    --limit 100
```

### Check Specific Analysis

```bash
gcloud run services logs read nba-props-analyzer-v2 \
    --region us-central1 \
    --limit 200 | grep -A 10 "EDGE FOUND"
```

## 🐛 Troubleshooting

### No Edges Found

**Possible causes:**
1. Lines are accurate (no real edges exist)
2. Player names don't match exactly
3. No games scheduled today
4. BallDontLie API issues

**Check logs:**
```bash
gcloud run services logs read nba-props-analyzer-v2 --region us-central1 --limit 50
```

Look for:
- `✗ Player not found` - Fix player names in sheet
- `⚠️ No game found today` - Normal if no games scheduled
- `Error fetching` - API issues (retry later)

### Timeout Errors

Increase timeout:
```bash
gcloud run services update nba-props-analyzer-v2 \
    --region us-central1 \
    --timeout 240
```

### Memory Issues

Increase memory:
```bash
gcloud run services update nba-props-analyzer-v2 \
    --region us-central1 \
    --memory 2Gi
```

## 🔒 Security

### Use Secret Manager (Recommended)

```bash
# Create secrets
echo -n "your-api-key" | gcloud secrets create balldontlie-key \
    --data-file=-

# Update service to use secret
gcloud run services update nba-props-analyzer-v2 \
    --region us-central1 \
    --set-secrets=BALLDONTLIE_API_KEY=balldontlie-key:latest
```

## 💰 Cost Estimate

- **Cloud Run**: $0-3/month (depends on runs/day)
- **Cloud Scheduler**: Free (first 3 jobs)
- **BallDontLie API**: Varies by tier
- **Total**: ~$1-5/month

## 📈 Performance

- **Analysis time**: 30-90 seconds for 10 props
- **API calls per prop**: 5-8 calls (player, games, opponent stats, injuries)
- **Memory usage**: 200-500MB
- **Suitable for**: 1-20 props per run

## 🎯 Next Steps

1. ✅ Deploy to Cloud Run
2. ✅ Test with real props
3. ✅ Set up Cloud Scheduler
4. ✅ Monitor for a few days
5. ✅ Adjust thresholds as needed

---

**Your advanced NBA props analyzer is ready!** 🏀📊

Questions? Check the code comments or logs for detailed information.
