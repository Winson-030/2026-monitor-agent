# デプロイガイド

> ⚠️ **本文档为快速参考。完整なデプロイガイドは [English Version](DEPLOYMENT_en.md) を参照してください**

---

## 📋 前提条件

- GCP プロジェクトと有効な請求先アカウント
- gcloud CLI がインストール済み
- Telegram Bot Token

## 🚀 クイックデプロイ

### 1. GCP プロジェクトの設定

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
gcloud config set project $PROJECT_ID
```

### 2. API の有効化

```bash
gcloud services enable run.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 3. GCS バケットの作成

```bash
export BUCKET_NAME="${PROJECT_ID}-inspection"
gcloud storage buckets create gs://${BUCKET_NAME} --location=${REGION}
```

### 4. Cloud Run へのデプロイ

```bash
# イメージのビルド
gcloud builds submit --tag gcr.io/${PROJECT_ID}/gcp-monitor

# デプロイ
gcloud run deploy gcp-monitor \
  --image gcr.io/${PROJECT_ID}/gcp-monitor \
  --region ${REGION} \
  --set-env-vars="TELEGRAM_BOT_TOKEN=your-token" \
  --set-env-vars="TELEGRAM_CHAT_ID=your-chat-id"
```

### 5. Cloud Scheduler の設定

```bash
export SERVICE_URL=$(gcloud run services describe gcp-monitor --region ${REGION} --format 'value(status.url)')

gcloud scheduler jobs create http gcp-monitor-scheduler \
  --schedule="*/5 * * * *" \
  --uri="${SERVICE_URL}/run-inspection" \
  --http-method=POST \
  --location=${REGION}
```

## 📚 完全なドキュメント

- [完全なデプロイガイド (English)](DEPLOYMENT_en.md)
- [設定ガイド (English)](CONFIGURATION_en.md)
- [メインドキュメント (English)](../README.md)
