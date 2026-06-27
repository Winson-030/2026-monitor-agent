# 配置指南

本文档详细说明 GCP Monitoring Agent 的所有配置选项，包括 `config.yaml` 各字段说明、环境变量以及阈值配置建议。

## 📄 配置文件

### config.yaml 完整示例

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

### 字段详解

#### `gcp` 配置块

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `project_id` | string | ✅ | - | GCP 项目 ID |
| `region` | string | - | `us-central1` | 默认 GCP 区域 |
| `default_zone` | string | - | `us-central1-a` | 默认可用区 |

#### `thresholds` 配置块

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `cpu_critical` | integer | - | 90 | CPU 使用率危急阈值 |
| `cpu_warning` | integer | - | 80 | CPU 使用率警告阈值 |
| `disk_critical` | integer | - | 90 | 磁盘使用率危急阈值 |
| `disk_warning` | integer | - | 80 | 磁盘使用率警告阈值 |

#### `gcs_bucket`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `gcs_bucket` | string | ✅ | GCS Bucket 名称，用于存储巡检报告。需预先创建并具有写入权限。 |

#### `budget` 配置块

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `daily_max_usd` | float | - | 3.0 | 每日预算上限（USD）。目前为预留字段，用于未来预算控制功能。 |

#### `inspection` 配置块

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `zones` | array | - | 巡检的可用区列表。通过 API 调用时可覆盖此配置。 |

---

## 🔐 环境变量

### 必需环境变量

| 变量名 | 说明 | 获取方式 |
|--------|------|----------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | @BotFather → /newbot |
| `TELEGRAM_CHAT_ID` | Telegram 聊天 ID | 调用 getUpdates API |

### 可选环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `GOOGLE_CLOUD_PROJECT` | GCP 项目 ID | gcloud 默认配置 |
| `GOOGLE_APPLICATION_CREDENTIALS` | 服务账号密钥文件路径 | gcloud 默认凭证 |
| `GCS_BUCKET` | GCS Bucket 名称（覆盖 config.yaml） | config.yaml 中的值 |

### 本地开发环境变量配置

创建 `.env` 文件：

```bash
# Telegram Bot 配置
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# GCP 配置（可选，优先使用 config.yaml）
# GOOGLE_CLOUD_PROJECT=your-project-id
# GCS_BUCKET=your-bucket-name
```

加载环境变量：

```bash
# Linux/Mac
export $(cat .env | xargs)

# 或安装 python-dotenv
pip install python-dotenv
```

---

## 📊 阈值配置建议

### CPU 使用率阈值

| 环境 | Warning | Critical | 说明 |
|------|---------|----------|------|
| 开发环境 | 70% | 85% | 资源受限，阈值较低 |
| 生产环境 | 80% | 90% | 稳定运行，阈值适中 |
| 高负载环境 | 85% | 95% | 预期高负载，阈值较高 |

### 磁盘使用率阈值

| 环境 | Warning | Critical | 说明 |
|------|---------|----------|------|
| 通用 | 80% | 90% | 预留空间用于日志和临时文件 |
| 数据库 | 70% | 85% | 数据库需要更多可用空间 |
| 日志服务 | 85% | 95% | 日志可压缩/轮转 |

### Gemini AI 分析阈值

```python
# AI 分析时会参考的阈值（在 agents/prompts.py 中定义）
SYSTEM_PROMPT = """你是 GCP 巡检分析器。
输入是一组采集好的指标 (CPU/磁盘/状态)。
对照阈值判断每个资源的状态: ok / warning / critical。
输出 JSON: [{"target": "vm-1", "status": "ok", "reason": "..."}, ...]
阈值: CPU > 90% = critical, > 80% = warning, 其他 = ok。"""
```

**注意**：AI 分析时会结合多个指标综合判断，而非简单阈值比较。

---

## 🌍 GCP 区域和可用区

### 常用区域

| 区域 | 代码 | 适用场景 |
|------|------|----------|
| 美国中部 | `us-central1` | 北美业务，成本较低 |
| 美国西部 | `us-west1` | 美国西海岸 |
| 美国东部 | `us-east1` | 美国东海岸 |
| 欧洲西部 | `europe-west1` | 欧洲业务 |
| 亚洲东部 | `asia-east1` | 台湾，亚洲业务 |
| 亚洲东北部 | `asia-northeast1` | 日本东京 |
| 亚洲东南部 | `asia-southeast1` | 新加坡 |

### 可用区配置

```yaml
inspection:
  zones:
    - "us-central1-a"    # 可用区 a
    - "us-central1-b"    # 可用区 b
    - "us-central1-c"    # 可用区 c
```

**最佳实践**：
- 同一区域的可用区通常距离较近（<5ms 延迟）
- 跨可用区部署可实现高可用
- 每个可用区的资源是独立的

---

## 🔧 高级配置

### 自定义配置示例

```yaml
# 生产环境配置
gcp:
  project_id: "prod-monitoring-2026"
  region: "asia-northeast1"           # 东京区域
  default_zone: "asia-northeast1-a"

thresholds:
  # 更严格的阈值
  cpu_critical: 85
  cpu_warning: 75
  disk_critical: 85
  disk_warning: 75

gcs_bucket: "prod-monitoring-reports"

budget:
  daily_max_usd: 10.0                  # 更高预算

inspection:
  zones:
    - "asia-northeast1-a"
    - "asia-northeast1-b"
    - "asia-northeast1-c"
```

```yaml
# 多区域配置
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
    # 美国
    - "us-central1-a"
    - "us-central1-b"
    - "us-west1-a"
    - "us-east1-b"
    # 欧洲
    - "europe-west1-b"
    - "europe-west1-c"
    # 亚洲
    - "asia-northeast1-a"
    - "asia-southeast1-b"
```

---

## 📝 配置验证

### 手动验证

```bash
# 验证 YAML 格式
python -c "import yaml; yaml.safe_load(open('config.yaml'))" && echo "✅ YAML valid"

# 验证 GCP 连接
gcloud config get-value project
gcloud projects describe $(gcloud config get-value project)

# 验证 GCS Bucket
gcloud storage buckets describe gs://your-bucket-name
```

### 配置热重载

当前版本需要重启服务以加载新配置。Cloud Run 会自动在重新部署时加载新配置：

```bash
# 修改 config.yaml 后重新部署
gcloud builds submit --tag gcr.io/$PROJECT_ID/gcp-monitor
gcloud run deploy gcp-monitor --image gcr.io/$PROJECT_ID/gcp-monitor --region us-central1
```
