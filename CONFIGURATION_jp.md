# 設定ガイド

このドキュメントでは、GCP Monitoring Agent のすべての設定オプションについて詳しく説明します。`config.yaml` の各フィールドの説明、環境変数、およびしきい値設定の推奨事項を含みます。

## 📄 設定ファイル

### config.yaml 完全な例

```yaml
gcp:
  project_id: "ai-hack-2026-winson"
  region: "us-central1"
  default_zone: "us-central1-a"

thresholds:
  cpu_critical: 90
  cpu_warning: 80
  disk_critical: 90
  disk_warning: 80

gcs_bucket: "ai-hack-2026-winson-inspection"

budget:
  daily_max_usd: 3.0

inspection:
  zones:
    - "us-central1-a"
    - "us-central1-b"
```

### フィールド詳細

#### `gcp` 設定ブロック

| フィールド | タイプ | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `project_id` | string | ✅ | - | GCP プロジェクト ID |
| `region` | string | - | `us-central1` | デフォルトの GCP リージョン |
| `default_zone` | string | - | `us-central1-a` | デフォルトのゾーン |

#### `thresholds` 設定ブロック

| フィールド | タイプ | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `cpu_critical` | integer | - | 90 | CPU 使用率のクリティカルしきい値 |
| `cpu_warning` | integer | - | 80 | CPU 使用率の警告しきい値 |
| `disk_critical` | integer | - | 90 | ディスク使用率のクリティカルしきい値 |
| `disk_warning` | integer | - | 80 | ディスク使用率の警告しきい値 |

#### `gcs_bucket`

| フィールド | タイプ | 必須 | 説明 |
|------|------|------|------|
| `gcs_bucket` | string | ✅ | 監査レポートを保存する GCS バケット名。書き込み権限付きで事前に作成が必要。 |

#### `budget` 設定ブロック

| フィールド | タイプ | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `daily_max_usd` | float | - | 3.0 | 1日あたりの予算上限（USD）。将来の予算制御機能用の予約フィールド。 |

#### `inspection` 設定ブロック

| フィールド | タイプ | 必須 | 説明 |
|------|------|------|------|
| `zones` | array | - | 監査対象のゾーンリスト。API 呼び出しで上書き可能。 |

---

## 🔐 環境変数

### 必須環境変数

| 変数名 | 説明 | 取得方法 |
|--------|------|----------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | @BotFather → /newbot |
| `TELEGRAM_CHAT_ID` | Telegram チャット ID | getUpdates API を呼び出す |

### 任意環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|--------|
| `GOOGLE_CLOUD_PROJECT` | GCP プロジェクト ID | gcloud のデフォルト設定 |
| `GOOGLE_APPLICATION_CREDENTIALS` | サービスアカウントキーのファイルパス | gcloud のデフォルト認証情報 |
| `GCS_BUCKET` | GCS バケット名（config.yaml を上書き） | config.yaml の値 |

### ローカル開発の環境変数設定

`.env` ファイルを作成：

```bash
# Telegram Bot 設定
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# GCP 設定（オプション、config.yaml が優先）
# GOOGLE_CLOUD_PROJECT=your-project-id
# GCS_BUCKET=your-bucket-name
```

環境変数を読み込む：

```bash
# Linux/Mac
export $(cat .env | xargs)

# または python-dotenv をインストール
pip install python-dotenv
```

---

## 📊 しきい値設定の推奨事項

### CPU 使用率のしきい値

| 環境 | Warning | Critical | 説明 |
|------|---------|----------|------|
| 開発環境 | 70% | 85% | リソースが制限されているため、しきい値は低め |
| 本番環境 | 80% | 90% | 安定稼働を考慮し、適切なしきい値に設定 |
| 高負荷環境 | 85% | 95% | 高負荷が予想されるため、しきい値は高め |

### ディスク使用率のしきい値

| 環境 | Warning | Critical | 説明 |
|------|---------|----------|------|
| 汎用 | 80% | 90% | ログと一時ファイル用にスペースを確保 |
| データベース | 70% | 85% | データベースはより多くの空き領域が必要 |
| ログサービス | 85% | 95% | ログは圧縮・ローテーション可能 |

### Gemini AI 分析のしきい値

```python
# AI が参照するしきい値（agents/prompts.py で定義）
SYSTEM_PROMPT = """あなたは GCP 監査アナライザーです。
入力は収集されたメトリクス（CPU/ディスク/ステータス）のセットです。
しきい値と比較してステータスを判定してください: ok / warning / critical。
出力 JSON: [{"target": "vm-1", "status": "ok", "reason": "..."}, ...]
しきい値: CPU > 90% = critical, > 80% = warning, その他 = ok。"""
```

**注記**: AI 分析は複数のメトリクスを組み合わせて包括的に評価し、単純なしきい値比較だけではありません。

---

## 🌍 GCP リージョンとゾーン

### 一般的なリージョン

| リージョン | コード | ユースケース |
|--------|------|----------|
| 米国中部 | `us-central1` | 北米、低コスト |
| 米国西部 | `us-west1` | 米国西海岸 |
| 米国東部 | `us-east1` | 米国東海岸 |
| 欧州西部 | `europe-west1` | 欧州の運用 |
| アジア東部 | `asia-east1` | 台湾、アジアの運用 |
| アジア北東部 | `asia-northeast1` | 東京、日本 |
| アジア南東部 | `asia-southeast1` | シンガポール |

### ゾーン設定

```yaml
inspection:
  zones:
    - "us-central1-a"    # ゾーン a
    - "us-central1-b"    # ゾーン b
    - "us-central1-c"    # ゾーン c
```

**ベストプラクティス**：
- 同じリージョン内のゾーンは通常近接している（<5ms レイテンシ）
- クロスゾーン展開で高可用性を実現
- 各ゾーンのリソースは独立している

---

## 🔧 高度な設定

### カスタム設定の例

```yaml
# 本番環境
gcp:
  project_id: "prod-monitoring-2026"
  region: "asia-northeast1"           # 東京リージョン
  default_zone: "asia-northeast1-a"

thresholds:
  # より厳格なしきい値
  cpu_critical: 85
  cpu_warning: 75
  disk_critical: 85
  disk_warning: 75

gcs_bucket: "prod-monitoring-reports"

budget:
  daily_max_usd: 10.0                  # より高い予算

inspection:
  zones:
    - "asia-northeast1-a"
    - "asia-northeast1-b"
    - "asia-northeast1-c"
```

```yaml
# マルチリージョン設定
gcp:
  project_id: "global-monitoring"
  region: "us-central1"
  default_zone: "us-central1-a"

thresholds:
  cpu_critical: 90
  cpu_warning: 80

gcs_bucket: "global-monitoring-data"

inspection:
  zones:
    # 米国
    - "us-central1-a"
    - "us-central1-b"
    - "us-west1-a"
    - "us-east1-b"
    # 欧州
    - "europe-west1-b"
    - "europe-west1-c"
    # アジア
    - "asia-northeast1-a"
    - "asia-southeast1-b"
```

---

## 📝 設定の検証

### 手動検証

```bash
# YAML 形式の検証
python -c "import yaml; yaml.safe_load(open('config.yaml'))" && echo "✅ YAML valid"

# GCP 接続の確認
gcloud config get-value project
gcloud projects describe $(gcloud config get-value project)

# GCS バケットの確認
gcloud storage buckets describe gs://your-bucket-name
```

### 設定の再読み込み

現在のバージョンでは、新しい設定を読み込むためにサービスの再起動が必要です。Cloud Run は再デプロイ時に自動的に新しい設定を読み込みます：

```bash
# config.yaml 変更後に再デプロイ
gcloud builds submit --tag gcr.io/$PROJECT_ID/gcp-monitor
gcloud run deploy gcp-monitor --image gcr.io/$PROJECT_ID/gcp-monitor --region us-central1
```
