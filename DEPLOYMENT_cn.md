# 部署指南

> ⚠️ **本文档为快速参考。完整部署指南请参阅 [English Version](DEPLOYMENT_en.md)**

---

## 📋 前置准备

- GCP 项目并启用计费
- gcloud CLI 已安装
- Telegram Bot Token

## 🚀 快速部署

### 1. 配置 GCP 项目

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
gcloud config set project $PROJECT_ID
```

### 2. 启用 API

```bash
gcloud services enable run.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 3. 创建 GCS Bucket

```bash
export BUCKET_NAME="${PROJECT_ID}-inspection"
gcloud storage buckets create gs://${BUCKET_NAME} --location=${REGION}
```

### 4. 部署到 Cloud Run

```bash
# 构建镜像
gcloud builds submit --tag gcr.io/${PROJECT_ID}/gcp-monitor

# 部署
gcloud run deploy gcp-monitor \
  --image gcr.io/${PROJECT_ID}/gcp-monitor \
  --region ${REGION} \
  --set-env-vars="TELEGRAM_BOT_TOKEN=your-token" \
  --set-env-vars="TELEGRAM_CHAT_ID=your-chat-id"
```

### 5. 配置 Cloud Scheduler

```bash
export SERVICE_URL=$(gcloud run services describe gcp-monitor --region ${REGION} --format 'value(status.url)')

gcloud scheduler jobs create http gcp-monitor-scheduler \
  --schedule="*/5 * * * *" \
  --uri="${SERVICE_URL}/run-inspection" \
  --http-method=POST \
  --location=${REGION}
```

## 📚 完整文档

- [完整部署指南 (English)](DEPLOYMENT_en.md)
- [配置指南 (English)](CONFIGURATION_en.md)
- [主文档 (English)](../README.md)
