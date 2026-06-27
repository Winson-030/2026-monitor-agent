# デプロイガイド

このドキュメントでは、GCP Monitoring Agent を GCP プロジェクトの準備から本番環境へのデプロイまで、一連の手順を詳しく説明します。

## 📋 前提条件

### 1. GCP プロジェクト要件

- **GCP プロジェクト** - 有効化済みの GCP プロジェクト
- **請求先アカウント** - 有効な請求先アカウントが紐付いていること
- **権限** - プロジェクトの Owner、または以下のロールを保有していること：
  - `roles/run.admin`
  - `roles/storage.admin`
  - `roles/monitoring.viewer`
  - `roles/compute.viewer`
  - `roles/aiplatform.user`

### 2. ローカルツール

```bash
# gcloud CLI がインストール済みであることを確認
gcloud version

# ログイン済みであることを確認
gcloud auth login
gcloud auth application-default login
```

### 3. Telegram Bot の準備

1. Telegram で `@BotFather` を検索
2. `/newbot` を送信して新しい Bot を作成
3. Bot Token を保存（形式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）
4. `/setcommands` を送信してコマンドメニューを設定

---

## 🚀 デプロイ手順

### ステップ 1：GCP プロジェクトの設定

```bash
# プロジェクト変数を設定
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export ZONE="us-central1-a"

# gcloud を設定
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE
```

### ステップ 2：必要な API を有効化

```bash
# Cloud Run を有効化
gcloud services enable run.googleapis.com

# Cloud Monitoring を有効化
gcloud services enable monitoring.googleapis.com

# Compute Engine を有効化
gcloud services enable compute.googleapis.com

# Cloud Storage を有効化
gcloud services enable storage.googleapis.com

# Vertex AI (Gemini) を有効化
gcloud services enable aiplatform.googleapis.com

# Cloud Build を有効化
gcloud services enable cloudbuild.googleapis.com

# Cloud Scheduler を有効化
gcloud services enable cloudscheduler.googleapis.com

# API ステータスを確認
gcloud services list --enabled | grep -E "(run|monitoring|compute|storage|aiplatform|cloudbuild|scheduler)"
```

### ステップ 3：GCS Bucket の作成

```bash
# 監査レポート用のバケットを作成
export BUCKET_NAME="${PROJECT_ID}-inspection"

gcloud storage buckets create gs://${BUCKET_NAME} \
  --location=${REGION} \
  --uniform-bucket-level-access \
  --public-access-prevention

# バケット作成の確認
gcloud storage buckets describe gs://${BUCKET_NAME}
```

### ステップ 4：サービスアカウントの権限設定

```bash
# デフォルトのサービスアカウントを取得
export SA_EMAIL="$(gcloud config get-value project)@appspot.gserviceaccount.com"

# Cloud Run のサービスアカウントを使用する場合
export SA_EMAIL="$(gcloud config get-value project)-compute@developer.gserviceaccount.com"

# 必要な権限を付与
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

### ステップ 5：設定ファイルの準備

```bash
# リポジトリをクローン
git clone https://github.com/Winson-030/2026-monitor-agent.git
cd gcp-monitoring-agent

# config.yaml を編集
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

### ステップ 6：Telegram Chat ID の取得

```bash
# 方法 1：curl を使用
export BOT_TOKEN="your-bot-token"

# まず Bot に任意のメッセージを送信してから実行：
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getUpdates" | grep -o '"chat":{"id":[0-9]*' | head -1

# 数字を CHAT_ID として抽出
export CHAT_ID="your-chat-id"
```

### ステップ 7：Cloud Run へのビルドとデプロイ

```bash
# 方法 1：Cloud Build を使用（推奨）
gcloud builds submit --tag gcr.io/${PROJECT_ID}/gcp-monitor

# 方法 2：ローカルビルド（Docker が必要）
# docker build -t gcr.io/${PROJECT_ID}/gcp-monitor .
# docker push gcr.io/${PROJECT_ID}/gcp-monitor

# Cloud Run にデプロイ
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

# サービス URL を取得
export SERVICE_URL=$(gcloud run services describe gcp-monitor --region ${REGION} --format 'value(status.url)')
echo "Service URL: ${SERVICE_URL}"
```

### ステップ 8：Cloud Scheduler の設定

```bash
# 5分間隔で実行されるスケジュールジョブを作成
gcloud scheduler jobs create http gcp-monitor-scheduler \
  --schedule="*/5 * * * *" \
  --uri="${SERVICE_URL}/run-inspection" \
  --http-method=POST \
  --message-body='{"zone":"'"${ZONE}"'"}' \
  --location=${REGION} \
  --time-zone="Asia/Tokyo"

# スケジューラーの確認
gcloud scheduler jobs describe gcp-monitor-scheduler --location=${REGION}

# 手動でテスト実行
gcloud scheduler jobs run gcp-monitor-scheduler --location=${REGION}
```

### ステップ 9：Telegram Webhook の設定（オプション）

```bash
# Telegram メッセージ受信用の Webhook を設定
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -d "url=${SERVICE_URL}/telegram-webhook"

# Webhook の確認
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
```

---

## 🔧 デプロイ後の検証

### 1. ヘルスチェックのテスト

```bash
curl "${SERVICE_URL}/healthz"
# 期待される出力: {"status":"ok"}
```

### 2. 手動での監査実行

```bash
curl -X POST "${SERVICE_URL}/run-inspection" \
  -H "Content-Type: application/json" \
  -d '{"zone":"'"${ZONE}"'"}'
```

### 3. Cloud Run ログの確認

```bash
# リアルタイムログ
gcloud logging tail "run.googleapis.com%2Fservices%2Fgcp-monitor" --format="value(textPayload)"

# Cloud Console を使用する場合
echo "https://console.cloud.google.com/run/detail/${REGION}/gcp-monitor/logs?project=${PROJECT_ID}"
```

### 4. 監査レポートの確認

```bash
# GCS からレポートをダウンロード
gcloud storage cat gs://${BUCKET_NAME}/inspection/latest_report.json | jq .
```

---

## 🛠️ デプロイの更新

### 新バージョンの再デプロイ

```bash
# コード変更後に再ビルド
gcloud builds submit --tag gcr.io/${PROJECT_ID}/gcp-monitor

# 再デプロイ（設定は維持）
gcloud run deploy gcp-monitor \
  --image gcr.io/${PROJECT_ID}/gcp-monitor \
  --region ${REGION}
```

### 環境変数の更新

```bash
gcloud run services update gcp-monitor \
  --region ${REGION} \
  --update-env-vars="TELEGRAM_CHAT_ID=new-chat-id"
```

### 設定の更新

`config.yaml` を変更してから、再ビルド・デプロイしてください。

---

## 🧹 リソースのクリーンアップ

```bash
# Cloud Scheduler を削除
gcloud scheduler jobs delete gcp-monitor-scheduler --location=${REGION}

# Cloud Run サービスを削除
gcloud run services delete gcp-monitor --region ${REGION}

# Container Registry イメージを削除（オプション）
gcloud container images delete gcr.io/${PROJECT_ID}/gcp-monitor --force-delete-tags

# GCS バケットを空にして削除
gcloud storage rm -r gs://${BUCKET_NAME}/*
gcloud storage buckets delete gs://${BUCKET_NAME}
```
