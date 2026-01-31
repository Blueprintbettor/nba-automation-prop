# QUICKSTART - Deploy in 5 Minutes

Get your NBA Props Analyzer running on Google Cloud Run in just a few commands.

## Prerequisites

- Google Cloud account with billing enabled
- `gcloud` CLI installed ([Install here](https://cloud.google.com/sdk/docs/install))
- Your Google Sheet ready with props
- Discord webhook URL

## Step-by-Step Deployment

### 1. Login and Setup Project (2 minutes)

```bash
# Login to Google Cloud
gcloud auth login

# Set your project ID (or create new)
export PROJECT_ID="nba-props-analyzer"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com sheets.googleapis.com
```

### 2. Create Service Account (1 minute)

```bash
# Create service account
gcloud iam service-accounts create nba-props-sa \
    --display-name="NBA Props Service Account"

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:nba-props-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/editor"
```

**⚠️ IMPORTANT**: Copy this email and share your Google Sheet with it (Viewer permission):
```
nba-props-sa@[YOUR-PROJECT-ID].iam.gserviceaccount.com
```

### 3. Deploy to Cloud Run (2 minutes)

```bash
# Set your environment variables
export SHEET_ID="1BEWBO-JZWQIjAtIgL69sK47ZXnLPwkE4VYI_uVVq8bg"
export DISCORD_WEBHOOK="https://discord.com/api/webhooks/1456668428784894184/QQeq0pHtiZWZqHpiQ2pyRxIf3CyZ64sqAohB0RW_yu_9oiWg1fEntfrlz88fV13_JXkp"

# Deploy!
gcloud run deploy nba-props-analyzer \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars SHEET_ID="$SHEET_ID" \
    --set-env-vars DISCORD_WEBHOOK_URL="$DISCORD_WEBHOOK" \
    --service-account nba-props-sa@$PROJECT_ID.iam.gserviceaccount.com
```

The deployment will:
- Build your Docker image
- Push to Google Container Registry
- Deploy to Cloud Run
- Give you a URL

### 4. Test It

```bash
# Get your service URL from the deployment output, then:
curl -X POST https://YOUR-SERVICE-URL.run.app/run
```

You should see a message in Discord! 🎉

## Optional: Set Up Daily Automation

Run automatically every day at 9 AM:

```bash
gcloud scheduler jobs create http nba-props-daily \
    --location us-central1 \
    --schedule "0 9 * * *" \
    --uri "https://YOUR-SERVICE-URL.run.app/run" \
    --http-method POST \
    --time-zone "America/Chicago"
```

## Troubleshooting

### "Permission denied" Error
→ Make sure you shared your Google Sheet with the service account email

### "Webhook failed" Error  
→ Double-check your Discord webhook URL

### "BallDontLie API" Error
→ Check player names match exactly (case-sensitive)

## What's Next?

- Update props in your Google Sheet
- Trigger analysis: `curl -X POST https://YOUR-URL/run`
- View logs: `gcloud run services logs tail nba-props-analyzer --region us-central1`
- See full docs: [README.md](README.md) and [DEPLOYMENT.md](DEPLOYMENT.md)

## Cost

With minimal usage: **~$0-2/month** (likely free tier)

---

That's it! Your analyzer is live. 🚀
