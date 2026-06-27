# Deployment Guide

This document provides detailed deployment steps for GCP Monitoring Agent, covering the complete process from GCP project preparation to production deployment.

## 📋 Prerequisites

### 1. GCP Project Requirements

- **GCP Project** - Active GCP project
- **Billing Account** - Associated billing account
- **Permissions** - Project Owner or the following roles:
  - `roles/run.admin`
  - `roles/storage.admin`
  - `roles/monitoring.viewer`
  - `roles/compute.viewer`
  - `roles/aiplatform.user`

### 2. Local Tools

```bash
# Verify gcloud CLI is installed
gcloud version

# Verify logged in
gcloud auth login
gcloud auth application-default login
```

### 3. Telegram Bot Setup

1. Search for `@BotFather` in Telegram
2. Send `/newbot` to create a new Bot
3. Save the Bot Token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
4. Send `/setcommands` to set command menu

---

## 🚀 Deployment Steps

### Step 1: Configure GCP Project

```bash
# Set project variables
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export ZONE="us-central1-a"

# Configure gcloud
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE
```

### Step 2: Enable Required APIs

```bash
# Enable Cloud Run
gcloud services enable run.googleapis.com

# Enable Cloud Monitoring
gcloud services enable monitoring.googleapis.com

# Enable Compute Engine
gcloud services enable compute.googleapis.com

# Enable Cloud Storage
gcloud services enable storage.googleapis.com

# Enable Vertex AI (Gemini)
gcloud services enable aiplatform.googleapis.com

# Enable Cloud Build
gcloud services enable cloudbuild.googleapis.com

# Enable Cloud Scheduler
gcloud services enable cloudscheduler.googleapis.com

# Verify API status
gcloud services list --enabled | grep -E "(run|monitoring|compute|storage|aiplatform|cloudbuild|scheduler)"
```

### Step 3: Create GCS Bucket

```bash
# Create bucket for inspection reports
export BUCKET_NAME="${PROJECT_ID}-inspection"

gcloud storage buckets create gs://${BUCKET_NAME} \
  --location=${REGION} \
  --uniform-bucket-level-access \
  --public-access-prevention

# Verify bucket creation
gcloud storage buckets describe gs://${BUCKET_NAME}
```

### Step 4: Configure Service Account Permissions

```bash
# Get default service account
export SA_EMAIL="$(gcloud config get-value project)@appspot.gserviceaccount.com"

# Or use Cloud Run service account
export SA_EMAIL="$(gcloud config get-value project)-compute@developer.gserviceaccount.com"

# Grant required permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/monitoring.viewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/compute.viewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/aiplatform.user"
```

### Step 5: Prepare Configuration

```bash
# Clone repository
git clone https://github.com/Winson-030/2026-monitor-agent.git
cd gcp-monitoring-agent

# Edit config.yaml
cat > config.yaml << EOF
gcp:
  project_id: "${PROJECT_ID}"
  region: "${REGION}"
  default_zone: "${ZONE}"

thresholds:
  cpu_critical: 90
  cpu_warning: 80
  disk_critical: 90
  disk_warning: 80

gcs_bucket: "${BUCKET_NAME}"

budget:
  daily_max_usd: 3.0

inspection:
  zones:
    - "${ZONE}"
EOF
```

### Step 6: Get Telegram Chat ID

```bash
# Method 1: Using curl
export BOT_TOKEN="your-bot-token"

# Send any message to the bot first, then run:
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getUpdates" | grep -o '"chat":{"id":[0-9]*' | head -1

# Extract the number as CHAT_ID
export CHAT_ID="your-chat-id"
```

### Step 7: Build and Deploy to Cloud Run

```bash
# Method 1: Using Cloud Build (recommended)
gcloud builds submit --tag gcr.io/${PROJECT_ID}/gcp-monitor

# Method 2: Local build (requires Docker)
# docker build -t gcr.io/${PROJECT_ID}/gcp-monitor .
# docker push gcr.io/${PROJECT_ID}/gcp-monitor

# Deploy to Cloud Run
gcloud run deploy gcp-monitor \
  --image gcr.io/${PROJECT_ID}/gcp-monitor \
  --region ${REGION} \
  --platform managed \
  --memory 512Mi \
  --cpu 1 \
  --concurrency 80 \
  --max-instances 5 \
  --min-instances 0 \
  --timeout 300 \
  --set-env-vars="TELEGRAM_BOT_TOKEN=${BOT_TOKEN}" \
  --set-env-vars="TELEGRAM_CHAT_ID=${CHAT_ID}" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --service-account ${SA_EMAIL} \
  --allow-unauthenticated \
  --no-cpu-boost

# Get service URL
export SERVICE_URL=$(gcloud run services describe gcp-monitor --region ${REGION} --format 'value(status.url)')
echo "Service URL: ${SERVICE_URL}"
```

### Step 8: Configure Cloud Scheduler

```bash
# Create scheduled job (every 5 minutes)
gcloud scheduler jobs create http gcp-monitor-scheduler \
  --schedule="*/5 * * * *" \
  --uri="${SERVICE_URL}/run-inspection" \
  --http-method=POST \
  --message-body='{"zone":"'"${ZONE}"'"}' \
  --location=${REGION} \
  --time-zone="Asia/Tokyo"

# Verify scheduler
gcloud scheduler jobs describe gcp-monitor-scheduler --location=${REGION}

# Run manually for testing
gcloud scheduler jobs run gcp-monitor-scheduler --location=${REGION}
```

### Step 9: Configure Telegram Webhook (Optional)

```bash
# Set webhook for receiving Telegram messages
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -d "url=${SERVICE_URL}/telegram-webhook"

# Verify webhook
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
```

---

## 🔧 Post-Deployment Verification

### 1. Test Health Check

```bash
curl "${SERVICE_URL}/healthz"
# Expected output: {"status":"ok"}
```

### 2. Trigger Inspection Manually

```bash
curl -X POST "${SERVICE_URL}/run-inspection" \
  -H "Content-Type: application/json" \
  -d '{"zone":"'"${ZONE}"'"}'
```

### 3. View Cloud Run Logs

```bash
# Real-time logs
gcloud logging tail "run.googleapis.com%2Fservices%2Fgcp-monitor" --format="value(textPayload)"

# Or use Cloud Console
echo "https://console.cloud.google.com/run/detail/${REGION}/gcp-monitor/logs?project=${PROJECT_ID}"
```

### 4. View Inspection Report

```bash
# Download report from GCS
gcloud storage cat gs://${BUCKET_NAME}/inspection/latest_report.json | jq .
```

---

## 🛠️ Update Deployment

### Redeploy New Version

```bash
# Rebuild after code changes
gcloud builds submit --tag gcr.io/${PROJECT_ID}/gcp-monitor

# Redeploy (keeps configuration)
gcloud run deploy gcp-monitor \
  --image gcr.io/${PROJECT_ID}/gcp-monitor \
  --region ${REGION}
```

### Update Environment Variables

```bash
gcloud run services update gcp-monitor \
  --region ${REGION} \
  --update-env-vars="TELEGRAM_CHAT_ID=new-chat-id"
```

---

## 🧹 Cleanup Resources

```bash
# Delete Cloud Scheduler
gcloud scheduler jobs delete gcp-monitor-scheduler --location=${REGION}

# Delete Cloud Run service
gcloud run services delete gcp-monitor --region ${REGION}

# Delete Container Registry image (optional)
gcloud container images delete gcr.io/${PROJECT_ID}/gcp-monitor --force-delete-tags

# Empty and delete GCS bucket
gcloud storage rm -r gs://${BUCKET_NAME}/*
gcloud storage buckets delete gs://${BUCKET_NAME}
```
