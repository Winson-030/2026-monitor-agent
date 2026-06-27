# 部署指南 / Deployment Guide

<p align="center">
  <a href="#中文">中文</a> | <a href="#english">English</a>
</p>

---

<h2 id="中文">中文</h2>

本文档提供详细的 GCP Monitoring Agent 部署步骤，涵盖从 GCP 项目准备到生产环境部署的完整流程。

## 📋 前置准备

### 1. GCP 项目要求

- **GCP 项目** - 已启用的 GCP 项目
- **计费账户** - 关联有效计费账户
- **权限** - 项目 Owner 或具有以下角色：
  - `roles/run.admin`
  - `roles/storage.admin`
  - `roles/monitoring.viewer`
  - `roles/compute.viewer`
  - `roles/aiplatform.user`

### 2. 本地工具

```bash
# 确认 gcloud CLI 已安装
gcloud version

# 确认已登录
gcloud auth login
gcloud auth application-default login
```

### 3. Telegram Bot 准备

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 创建新 Bot
3. 保存 Bot Token（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）
4. 发送 `/setcommands` 设置命令菜单

---

## 🚀 部署步骤

### 第一步：配置 GCP 项目

```bash
# 设置项目变量
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export ZONE="us-central1-a"

# 配置 gcloud
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE
```

### 第二步：启用所需 API

```bash
# 启用 Cloud Run
gcloud services enable run.googleapis.com

# 启用 Cloud Monitoring
gcloud services enable monitoring.googleapis.com

# 启用 Compute Engine
gcloud services enable compute.googleapis.com

# 启用 Cloud Storage
gcloud services enable storage.googleapis.com

# 启用 Vertex AI (Gemini)
gcloud services enable aiplatform.googleapis.com

# 启用 Cloud Build
gcloud services enable cloudbuild.googleapis.com

# 启用 Cloud Scheduler
gcloud services enable cloudscheduler.googleapis.com

# 验证 API 状态
gcloud services list --enabled | grep -E "(run|monitoring|compute|storage|aiplatform|cloudbuild|scheduler)"
```

### 第三步：创建 GCS Bucket

```bash
# 创建存储桶（用于保存巡检报告）
export BUCKET_NAME="${PROJECT_ID}-inspection"

gcloud storage buckets create gs://${BUCKET_NAME} \
  --location=${REGION} \
  --uniform-bucket-level-access \
  --public-access-prevention

# 验证 Bucket 创建
gcloud storage buckets describe gs://${BUCKET_NAME}
```

### 第四步：配置服务账号权限

```bash
# 获取默认服务账号
export SA_EMAIL="$(gcloud config get-value project)@appspot.gserviceaccount.com"

# 或使用 Cloud Run 服务账号
export SA_EMAIL="$(gcloud config get-value project)-compute@developer.gserviceaccount.com"

# 授予必要权限
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

### 第五步：准备配置文件

```bash
# 克隆仓库
git clone https://github.com/Winson-030/2026-monitor-agent.git
cd gcp-monitoring-agent

# 编辑 config.yaml
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

### 第六步：获取 Telegram Chat ID

```bash
# 方法 1：使用 curl 获取
export BOT_TOKEN="your-bot-token"

# 先给 Bot 发送任意消息，然后运行：
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getUpdates" | grep -o '"chat":{"id":[0-9]*' | head -1

# 提取数字作为 CHAT_ID
export CHAT_ID="your-chat-id"
```

### 第七步：构建并部署到 Cloud Run

```bash
# 方法 1：使用 Cloud Build（推荐）
gcloud builds submit --tag gcr.io/${PROJECT_ID}/gcp-monitor

# 方法 2：本地构建（需要 Docker）
# docker build -t gcr.io/${PROJECT_ID}/gcp-monitor .
# docker push gcr.io/${PROJECT_ID}/gcp-monitor

# 部署到 Cloud Run
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

# 获取服务 URL
export SERVICE_URL=$(gcloud run services describe gcp-monitor --region ${REGION} --format 'value(status.url)')
echo "Service URL: ${SERVICE_URL}"
```

### 第八步：配置 Cloud Scheduler

```bash
# 创建每 5 分钟执行一次的调度任务
gcloud scheduler jobs create http gcp-monitor-scheduler \
  --schedule="*/5 * * * *" \
  --uri="${SERVICE_URL}/run-inspection" \
  --http-method=POST \
  --message-body='{"zone":"'"${ZONE}"'"}' \
  --location=${REGION} \
  --time-zone="Asia/Tokyo"

# 验证调度器
gcloud scheduler jobs describe gcp-monitor-scheduler --location=${REGION}

# 手动触发测试
gcloud scheduler jobs run gcp-monitor-scheduler --location=${REGION}
```

### 第九步：配置 Telegram Webhook（可选）

```bash
# 设置 Webhook（用于接收 Telegram 消息）
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -d "url=${SERVICE_URL}/telegram-webhook"

# 验证 Webhook
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
```

---

## 🔧 部署后验证

### 1. 测试健康检查

```bash
curl "${SERVICE_URL}/healthz"
# 预期输出: {"status":"ok"}
```

### 2. 手动触发巡检

```bash
curl -X POST "${SERVICE_URL}/run-inspection" \
  -H "Content-Type: application/json" \
  -d '{"zone":"'"${ZONE}"'"}'
```

### 3. 查看 Cloud Run 日志

```bash
# 实时日志
gcloud logging tail "run.googleapis.com%2Fservices%2Fgcp-monitor" --format="value(textPayload)"

# 或使用 Cloud Console
echo "https://console.cloud.google.com/run/detail/${REGION}/gcp-monitor/logs?project=${PROJECT_ID}"
```

### 4. 查看巡检报告

```bash
# 从 GCS 下载报告
gcloud storage cat gs://${BUCKET_NAME}/inspection/latest_report.json | jq .
```

---

## 🛠️ 更新部署

### 重新部署新版本

```bash
# 修改代码后重新构建
gcloud builds submit --tag gcr.io/${PROJECT_ID}/gcp-monitor

# 重新部署（保留配置）
gcloud run deploy gcp-monitor \
  --image gcr.io/${PROJECT_ID}/gcp-monitor \
  --region ${REGION}
```

### 更新环境变量

```bash
gcloud run services update gcp-monitor \
  --region ${REGION} \
  --update-env-vars="TELEGRAM_CHAT_ID=new-chat-id"
```

### 更新配置

修改 `config.yaml` 后重新构建部署即可。

---

## 🧹 清理资源

```bash
# 删除 Cloud Scheduler
gcloud scheduler jobs delete gcp-monitor-scheduler --location=${REGION}

# 删除 Cloud Run 服务
gcloud run services delete gcp-monitor --region ${REGION}

# 删除 Container Registry 镜像（可选）
gcloud container images delete gcr.io/${PROJECT_ID}/gcp-monitor --force-delete-tags

# 清空并删除 GCS Bucket
gcloud storage rm -r gs://${BUCKET_NAME}/*
gcloud storage buckets delete gs://${BUCKET_NAME}
```

---

<h2 id="english">🇺🇸 English</h2>

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
