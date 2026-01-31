# QUICKSTART - Deploy in 5 Minutes

Fast deployment guide for NBA Props Analyzer to Google Cloud Run.

## Prerequisites

✅ Google Cloud account with billing  
✅ `gcloud` CLI installed  
✅ Your credentials ready:
- Discord webhook URL
- Google Sheets ID  
- BallDontLie API key

## 5-Minute Deployment

### Step 1: Login & Setup (1 minute)

```bash
# Login
gcloud auth login

# Set project
export PROJECT_ID="nba-props-analyzer"
gcloud config set project $PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com sheets.googleapis.com
```

### Step 2: Create Service Account (1 minute)

```bash
# Create service account
gcloud iam service-accounts create nba-props-sa \
    --display-name="NBA Props Service Account"

# Grant permissions
PROJECT_ID=$(gcloud config get-value project)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:nba-props-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/editor"
```

**⚠️ IMPORTANT:** Share your Google Sheet with this email (Viewer permission):
```
nba-props-sa@[YOUR-PROJECT-ID].iam.gserviceaccount.com
```

### Step 3: Deploy (2 minutes)

```bash
# Set your values
export SHEET_ID="1BEWBO-JZWQIjAtIgL69sK47ZXnLPwkE4VYI_uVVq8bg"
export DISCORD_WEBHOOK="https://discord.com/api/webhooks/1456668428784894184/QQeq0pHtiZWZqHpiQ2pyRxIf3CyZ64sqAohB0RW_yu_9oiWg1fEntfrlz88fV13_JXkp"
export BALLDONTLIE_KEY="ccd6b645-9f53-476d-a7a6-dc46b5159003"

# Deploy!
gcloud run deploy nba-props-analyzer \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --service-account nba-props-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars SHEET_ID="$SHEET_ID",DISCORD_WEBHOOK_URL="$DISCORD_WEBHOOK",BALLDONTLIE_API_KEY="$BALLDONTLIE_KEY"
```

### Step 4: Test (1 minute)

```bash
# Get your service URL (from deployment output)
export SERVICE_URL="https://nba-props-analyzer-xxxxx-uc.a.run.app"

# Test it!
curl -X POST $SERVICE_URL/run
```

Check Discord - you should see your props analysis! 🎉

## Optional: Daily Automation

Run automatically every day at 9 AM:

```bash
gcloud services enable cloudscheduler.googleapis.com

SERVICE_URL=$(gcloud run services describe nba-props-analyzer \
    --region us-central1 \
    --format 'value(status.url)')

gcloud scheduler jobs create http nba-props-daily \
    --location us-central1 \
    --schedule "0 9 * * *" \
    --uri "${SERVICE_URL}/run" \
    --http-method POST \
    --time-zone "America/Chicago"
```

## Verify It Works

1. ✅ **Service deployed** - Check Cloud Run console
2. ✅ **Health check** - `curl https://YOUR-URL/`
3. ✅ **Run analysis** - `curl -X POST https://YOUR-URL/run`
4. ✅ **Discord message** - Check your Discord channel
5. ✅ **Logs working** - `gcloud run services logs tail nba-props-analyzer --region us-central1`

## Common Issues

### "Permission denied" on Google Sheets
→ Share sheet with service account email

### "Player not found"
→ Check player name spelling (case-sensitive)

### "Discord webhook failed"
→ Verify webhook URL is correct

### Build fails
→ Make sure you're in project directory with all files

## What's Next?

- **View logs**: `gcloud run services logs tail nba-props-analyzer --region us-central1`
- **Update env vars**: `gcloud run services update nba-props-analyzer --set-env-vars KEY=VALUE`
- **Redeploy**: `gcloud run deploy nba-props-analyzer --source .`
- **Delete**: `gcloud run services delete nba-props-analyzer --region us-central1`

## Full Documentation

- [README.md](README.md) - Complete documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Detailed deployment guide

---

**Done! Your analyzer is live.** 🚀

Estimated cost: **$0-2/month**
