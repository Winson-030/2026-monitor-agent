# Configuration Guide

This document details all configuration options for GCP Monitoring Agent, including `config.yaml` field descriptions, environment variables, and threshold recommendations.

## 📄 Configuration Files

### Complete config.yaml Example

```yaml
gcp:
  project_id: "ai-hack-2026-winson"     # GCP Project ID
  region: "us-central1"                  # Default region
  default_zone: "us-central1-a"          # Default zone

thresholds:
  cpu_critical: 90                       # CPU critical threshold (%)
  cpu_warning: 80                        # CPU warning threshold (%)
  disk_critical: 90                    # Disk critical threshold (%)
  disk_warning: 80                       # Disk warning threshold (%)

gcs_bucket: "ai-hack-2026-winson-inspection"  # GCS Bucket name

budget:
  daily_max_usd: 3.0                     # Daily budget limit (USD)

inspection:
  zones:                                 # Zones to inspect
    - "us-central1-a"
    - "us-central1-b"
```

### Field Reference

#### `gcp` Section

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `project_id` | string | ✅ | - | GCP Project ID for all API calls |
| `region` | string | - | `us-central1` | Default GCP region |
| `default_zone` | string | - | `us-central1-a` | Default zone for single-zone inspection |

#### `thresholds` Section

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `cpu_critical` | integer | - | 90 | CPU usage critical threshold |
| `cpu_warning` | integer | - | 80 | CPU usage warning threshold |
| `disk_critical` | integer | - | 90 | Disk usage critical threshold |
| `disk_warning` | integer | - | 80 | Disk usage warning threshold |

#### `gcs_bucket`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `gcs_bucket` | string | ✅ | GCS Bucket name for storing inspection reports. Must be pre-created with write permissions. |

#### `budget` Section

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `daily_max_usd` | float | - | 3.0 | Daily budget limit (USD). Reserved for future budget control features. |

#### `inspection` Section

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `zones` | array | - | List of zones to inspect. Can be overridden via API calls. |

---

## 🔐 Environment Variables

### Required Environment Variables

| Variable | Description | How to Get |
|----------|-------------|------------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | @BotFather → /newbot |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | Call getUpdates API |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT` | GCP Project ID | gcloud default configuration |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account key file path | gcloud default credentials |
| `GCS_BUCKET` | GCS Bucket name (overrides config.yaml) | Value from config.yaml |

### Local Development Setup

Create `.env` file:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# GCP Configuration (optional, config.yaml takes precedence)
# GOOGLE_CLOUD_PROJECT=your-project-id
# GCS_BUCKET=your-bucket-name
```

Load environment variables:

```bash
# Linux/Mac
export $(cat .env | xargs)

# Or install python-dotenv
pip install python-dotenv
```

---

## 📊 Threshold Recommendations

### CPU Usage Thresholds

| Environment | Warning | Critical | Notes |
|-------------|---------|----------|-------|
| Development | 70% | 85% | Resource constrained, lower thresholds |
| Production | 80% | 90% | Stable operation, moderate thresholds |
| High Load | 85% | 95% | Expected high load, higher thresholds |

### Disk Usage Thresholds

| Environment | Warning | Critical | Notes |
|-------------|---------|----------|-------|
| General | 80% | 90% | Reserve space for logs and temp files |
| Database | 70% | 85% | Databases need more free space |
| Log Service | 85% | 95% | Logs can be compressed/rotated |

### Gemini AI Analysis Thresholds

```python
# Thresholds referenced by AI (defined in agents/prompts.py)
SYSTEM_PROMPT = """You are a GCP inspection analyzer.
Input is a set of collected metrics (CPU/disk/status).
Compare against thresholds to determine status: ok / warning / critical.
Output JSON: [{"target": "vm-1", "status": "ok", "reason": "..."}, ...]
Thresholds: CPU > 90% = critical, > 80% = warning, others = ok."""
```

**Note**: AI analysis combines multiple metrics for holistic assessment, not just simple threshold comparison.

---

## 🌍 GCP Regions and Zones

### Common Regions

| Region | Code | Use Case |
|--------|------|----------|
| US Central | `us-central1` | North America, lower cost |
| US West | `us-west1` | US West Coast |
| US East | `us-east1` | US East Coast |
| Europe West | `europe-west1` | Europe operations |
| Asia East | `asia-east1` | Taiwan, Asia operations |
| Asia Northeast | `asia-northeast1` | Tokyo, Japan |
| Asia Southeast | `asia-southeast1` | Singapore |

### Zone Configuration

```yaml
inspection:
  zones:
    - "us-central1-a"    # Zone a
    - "us-central1-b"    # Zone b
    - "us-central1-c"    # Zone c
```

**Best Practices**:
- Zones in the same region are typically close (<5ms latency)
- Cross-zone deployment enables high availability
- Resources in each zone are isolated

---

## 🔧 Advanced Configuration

### Custom Configuration Examples

```yaml
# Production environment
gcp:
  project_id: "prod-monitoring-2026"
  region: "asia-northeast1"           # Tokyo region
  default_zone: "asia-northeast1-a"

thresholds:
  # Stricter thresholds
  cpu_critical: 85
  cpu_warning: 75
  disk_critical: 85
  disk_warning: 75

gcs_bucket: "prod-monitoring-reports"

budget:
  daily_max_usd: 10.0                  # Higher budget

inspection:
  zones:
    - "asia-northeast1-a"
    - "asia-northeast1-b"
    - "asia-northeast1-c"
```

```yaml
# Multi-region configuration
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
    # US
    - "us-central1-a"
    - "us-central1-b"
    - "us-west1-a"
    - "us-east1-b"
    # Europe
    - "europe-west1-b"
    - "europe-west1-c"
    # Asia
    - "asia-northeast1-a"
    - "asia-southeast1-b"
```

---

## 📝 Configuration Validation

### Manual Validation

```bash
# Validate YAML format
python -c "import yaml; yaml.safe_load(open('config.yaml'))" && echo "✅ YAML valid"

# Verify GCP connection
gcloud config get-value project
gcloud projects describe $(gcloud config get-value project)

# Verify GCS Bucket
gcloud storage buckets describe gs://your-bucket-name
```

### Configuration Reload

Current version requires service restart to load new configuration. Cloud Run automatically loads new configuration on redeployment:

```bash
# Redeploy after modifying config.yaml
gcloud builds submit --tag gcr.io/$PROJECT_ID/gcp-monitor
gcloud run deploy gcp-monitor --image gcr.io/$PROJECT_ID/gcp-monitor --region us-central1
```
