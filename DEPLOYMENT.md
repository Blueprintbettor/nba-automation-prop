# Deployment Guide - Google Cloud Run

Complete guide for deploying NBA Props Automation to Google Cloud Run.

## Prerequisites

- Google Cloud account with billing enabled
- `gcloud` CLI installed ([Install here](https://cloud.google.com/sdk/docs/install))
- Your environment variables ready:
  - Discord webhook URL
  - Google Sheets ID
  - BallDontLie API key

## Step 1: Google Cloud Setup

### 1.1 Install gcloud CLI

```bash
# macOS
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Windows
# Download installer from: https://cloud.google.com/sdk/docs/install
```

### 1.2 Login and Initialize

```bash
# Login to Google Cloud
gcloud auth login

# Set your project ID (or create new)
export PROJECT_ID="nba-props-analyzer"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable sheets.googleapis.com
```

## Step 2: Service Account for Google Sheets

### 2.1 Create Service Account

```bash
# Create service account
gcloud iam service-accounts create nba-props-sa \
    --display-name="NBA Props Service Account" \
    --description="Service account for NBA Props Analyzer"

# Get project ID
PROJECT_ID=$(gcloud config get-value project)

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:nba-props-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/editor"
```

### 2.2 Share Google Sheet

**IMPORTANT:** Copy the service account email and share your Google Sheet with it:

```
nba-props-sa@[YOUR-PROJECT-ID].iam.gserviceaccount.com
```

**Steps:**
1. Open your Google Sheet
2. Click "Share" button
3. Paste the service account email
4. Set permission to **"Viewer"**
5. Uncheck "Notify people"
6. Click "Share"

## Step 3: Deploy to Cloud Run

### 3.1 Set Environment Variables

```bash
# Your environment variables
export SHEET_ID="1BEWBO-JZWQIjAtIgL69sK47ZXnLPwkE4VYI_uVVq8bg"
export DISCORD_WEBHOOK="https://discord.com/api/webhooks/1456668428784894184/QQeq0pHtiZWZqHpiQ2pyRxIf3CyZ64sqAohB0RW_yu_9oiWg1fEntfrlz88fV13_JXkp"
export BALLDONTLIE_KEY="ccd6b645-9f53-476d-a7a6-dc46b5159003"
export REGION="us-central1"  # Choose closest to you
```

### 3.2 Deploy Application

```bash
# Navigate to project directory
cd /path/to/nba-props-automation

# Deploy to Cloud Run
gcloud run deploy nba-props-analyzer \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --service-account nba-props-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars SHEET_ID="$SHEET_ID" \
    --set-env-vars DISCORD_WEBHOOK_URL="$DISCORD_WEBHOOK" \
    --set-env-vars BALLDONTLIE_API_KEY="$BALLDONTLIE_KEY" \
    --set-env-vars SHEET_RANGE="INPUT_LINES!A2:E50" \
    --timeout 120 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 1
```

**This will:**
- Build your Docker image using Cloud Build
- Deploy to Cloud Run
- Output a service URL

**Save the service URL!** It will look like:
```
https://nba-props-analyzer-xxxxx-uc.a.run.app
```

## Step 4: Test Deployment

### 4.1 Health Check

```bash
# Test health endpoint
curl https://YOUR-SERVICE-URL.run.app/

# Should return:
# {
#   "status": "healthy",
#   "service": "NBA Props Analyzer",
#   "version": "2.0",
#   ...
# }
```

### 4.2 Run Analysis

```bash
# Trigger analysis
curl -X POST https://YOUR-SERVICE-URL.run.app/run

# Should return:
# {
#   "ok": true,
#   "props_count": 5,
#   "summary": {...},
#   "discord_posted": true,
#   ...
# }
```

Check your Discord channel - you should see the props analysis!

## Step 5: Automated Scheduling (Optional)

Set up Cloud Scheduler to run automatically every day.

### 5.1 Enable Cloud Scheduler

```bash
gcloud services enable cloudscheduler.googleapis.com
```

### 5.2 Create Scheduler Job

```bash
# Get your service URL
SERVICE_URL=$(gcloud run services describe nba-props-analyzer \
    --region $REGION \
    --format 'value(status.url)')

# Create daily job at 9 AM Central Time
gcloud scheduler jobs create http nba-props-daily \
    --location $REGION \
    --schedule "0 9 * * *" \
    --uri "${SERVICE_URL}/run" \
    --http-method POST \
    --time-zone "America/Chicago" \
    --description "Daily NBA props analysis"
```

**Cron Schedule Examples:**
```
"0 9 * * *"      # Daily at 9 AM
"0 9 * * 1-5"    # Weekdays at 9 AM
"0 12,18 * * *"  # Twice daily at noon and 6 PM
"30 8 * * 2,4,6" # Tuesdays, Thursdays, Saturdays at 8:30 AM
```

### 5.3 Test Scheduler

```bash
# Manually trigger the scheduled job
gcloud scheduler jobs run nba-props-daily --location $REGION
```

## Managing the Deployment

### View Logs

```bash
# Stream logs in real-time
gcloud run services logs tail nba-props-analyzer --region $REGION

# View recent logs
gcloud run services logs read nba-props-analyzer \
    --region $REGION \
    --limit 100

# View logs from last hour
gcloud run services logs read nba-props-analyzer \
    --region $REGION \
    --limit 100 \
    --format "table(timestamp,severity,textPayload)"
```

### Update Environment Variables

```bash
# Update single variable
gcloud run services update nba-props-analyzer \
    --region $REGION \
    --set-env-vars SHEET_ID="new-sheet-id"

# Update multiple variables
gcloud run services update nba-props-analyzer \
    --region $REGION \
    --set-env-vars SHEET_ID="new-id",USE_SIMPLE_FORMAT="true"
```

### Redeploy with Code Changes

```bash
# After making code changes
gcloud run deploy nba-props-analyzer \
    --source . \
    --region $REGION
```

### Delete Service

```bash
# Delete Cloud Run service
gcloud run services delete nba-props-analyzer --region $REGION

# Delete scheduler job
gcloud scheduler jobs delete nba-props-daily --location $REGION

# Delete service account
gcloud iam service-accounts delete \
    nba-props-sa@$PROJECT_ID.iam.gserviceaccount.com
```

## Cost Estimation

### Cloud Run Pricing (2024)

**Free Tier (per month):**
- 2 million requests
- 360,000 GB-seconds of memory
- 180,000 vCPU-seconds

**Beyond Free Tier:**
- Requests: $0.40 per million
- Memory: $0.0000025 per GB-second
- CPU: $0.00002400 per vCPU-second

**Estimated Monthly Cost:**
- **Light use** (1-2 runs/day): **$0** (within free tier)
- **Medium use** (5-10 runs/day): **$0-1**
- **Heavy use** (hourly runs): **$1-3**

### Cloud Scheduler Pricing
- First 3 jobs: **FREE**
- Additional jobs: $0.10 per job per month

**Total estimated cost: $0-2/month**

## Troubleshooting

### Issue: "Permission denied" accessing Google Sheets

**Solution:**
1. Verify service account email: `nba-props-sa@[PROJECT_ID].iam.gserviceaccount.com`
2. Check if sheet is shared with this email
3. Ensure permission is set to "Viewer"
4. Try re-sharing the sheet

**Verify:**
```bash
# List service accounts
gcloud iam service-accounts list

# Describe service
gcloud run services describe nba-props-analyzer --region $REGION
```

### Issue: "BALLDONTLIE_API_KEY not set"

**Solution:**
```bash
# Check environment variables
gcloud run services describe nba-props-analyzer \
    --region $REGION \
    --format 'value(spec.template.spec.containers[0].env)'

# Update API key
gcloud run services update nba-props-analyzer \
    --region $REGION \
    --set-env-vars BALLDONTLIE_API_KEY="your-api-key"
```

### Issue: "Build failed"

**Solution:**
```bash
# Check Cloud Build logs
gcloud builds list --limit=5

# View specific build
gcloud builds log [BUILD_ID]

# Common issues:
# - Missing requirements.txt
# - Syntax errors in Python files
# - Docker build errors
```

### Issue: "Rate limit exceeded"

**Solution:**
- Check your BallDontLie API tier
- Paid tier should have high limits
- Consider adding delay between requests
- Contact BallDontLie support

### Issue: "Discord webhook failed"

**Solution:**
```bash
# Test webhook manually
curl -X POST "YOUR_WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d '{"content":"Test message"}'

# Check if webhook is still active in Discord
# Verify URL hasn't changed
```

### Issue: Service timing out

**Solution:**
```bash
# Increase timeout (default 60s, max 3600s)
gcloud run services update nba-props-analyzer \
    --region $REGION \
    --timeout 180

# Increase memory
gcloud run services update nba-props-analyzer \
    --region $REGION \
    --memory 1Gi
```

## Security Best Practices

### 1. Use Secret Manager (Recommended)

```bash
# Create secrets
echo -n "your-api-key" | gcloud secrets create balldontlie-api-key \
    --data-file=- \
    --replication-policy="automatic"

# Grant access to service account
gcloud secrets add-iam-policy-binding balldontlie-api-key \
    --member="serviceAccount:nba-props-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Update service to use secret
gcloud run services update nba-props-analyzer \
    --region $REGION \
    --set-secrets=BALLDONTLIE_API_KEY=balldontlie-api-key:latest
```

### 2. Restrict Access

```bash
# Remove public access
gcloud run services remove-iam-policy-binding nba-props-analyzer \
    --region $REGION \
    --member="allUsers" \
    --role="roles/run.invoker"

# Add Cloud Scheduler service account
gcloud run services add-iam-policy-binding nba-props-analyzer \
    --region $REGION \
    --member="serviceAccount:nba-props-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker"
```

### 3. Enable VPC Connector (Advanced)

For restricted outbound traffic to specific IPs.

## Monitoring

### Set Up Alerts

```bash
# Create alert for errors
gcloud alpha monitoring policies create \
    --notification-channels=[CHANNEL_ID] \
    --display-name="NBA Props Errors" \
    --condition-display-name="Error rate" \
    --condition-threshold-value=5 \
    --condition-threshold-duration=60s
```

### View Metrics

Access metrics in Cloud Console:
1. Go to Cloud Run
2. Click on service
3. View "METRICS" tab

**Key metrics:**
- Request count
- Request latency
- Error rate
- Memory usage
- CPU usage

## Next Steps

1. ✅ **Test thoroughly** - Run multiple times
2. ✅ **Set up monitoring** - Create alerts
3. ✅ **Schedule automation** - Cloud Scheduler
4. ✅ **Document** - Keep notes on custom configurations
5. ✅ **Backup** - Keep Google Sheet backed up

---

**Your NBA Props Analyzer is now live on Cloud Run!** 🚀

For questions or issues, refer to:
- [README.md](README.md) - Main documentation
- [Google Cloud Run Docs](https://cloud.google.com/run/docs)
- [BallDontLie API Docs](https://www.balldontlie.io/docs)
