# GCP Monitoring Agent

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?logo=python" alt="Python 3.13">
  <img src="https://img.shields.io/badge/Cloud%20Run-GCP-orange?logo=google-cloud" alt="Cloud Run">
  <img src="https://img.shields.io/badge/Gemini-2.5%20Flash-green?logo=google" alt="Gemini 2.5 Flash">
  <img src="https://img.shields.io/badge/License-MIT-blue" alt="License: MIT">
</p>

<p align="center">
  <b>中文</b> | <a href="#english">English</a>
</p>

## 📋 项目介绍

**GCP Monitoring Agent** 是一个智能的 GCP 资源巡检系统，部署于 Cloud Run，能够定时采集 GCE 实例指标，通过 Gemini 2.5 Flash AI 进行分析，并通过 Telegram Bot 推送告警。

### 核心特性

- 🤖 **AI 驱动分析** - 使用 Gemini 2.5 Flash 智能分析监控指标
- 📊 **自动指标采集** - 基于 GCP Monitoring API 的确定性数据采集
- 💬 **Telegram 集成** - Bot 交互支持 (`/status`, `/inspect` 命令)
- ☁️ **Cloud Run 部署** - 无服务器架构，按需付费
- 📁 **状态持久化** - GCS 存储巡检报告
- 🔧 **灵活配置** - YAML 配置 + 环境变量支持

---

## 🏗️ 架构图

```mermaid
flowchart TB
    subgraph Scheduler["Cloud Scheduler"]
        CS["定时触发<br/>每 5 分钟"]
    end

    subgraph CloudRun["Cloud Run Service"]
        Flask["Flask App<br/>Port 8080"]
        Fetcher["MetricsFetcher<br/>GCP Monitoring API"]
        Inspector["Inspector<br/>Gemini 2.5 Flash"]
        StateMgr["GCSStateManager<br/>Report Storage"]
    end

    subgraph GCP["GCP Resources"]
        GCE["Compute Engine"]
        Monitor["Cloud Monitoring"]
    end

    subgraph Storage["Cloud Storage"]
        GCS["GCS Bucket<br/>latest_report.json"]
    end

    subgraph Notification["Notification"]
        TG["Telegram Bot"]
    end

    CS -->|HTTP POST /run-inspection| Flask
    Flask --> Fetcher
    Fetcher -->|List Instances| GCE
    Fetcher -->|Query Metrics| Monitor
    Fetcher --> Inspector
    Inspector -->|AI Analysis| StateMgr
    StateMgr -->|Save Report| GCS
    Flask -->|Send Alert| TG

    TG -->|Webhook /telegram-webhook| Flask
    Flask -->|Load Report| StateMgr
    StateMgr -->|Read Report| GCS
```

### 组件说明

| 组件 | 说明 | 技术 |
|------|------|------|
| **MetricsFetcher** | 采集 GCE 实例的 CPU/磁盘/状态指标 | `google-cloud-monitoring`, `google-cloud-compute` |
| **Inspector** | Gemini AI 分析指标并判定状态 | `vertexai`, Gemini 2.5 Flash |
| **GCSStateManager** | 巡检报告存储与读取 | `google-cloud-storage` |
| **TelegramHandler** | Bot 消息推送与交互处理 | Telegram Bot API |
| **Orchestrator** | 巡检流程编排 | Python 类 |

---

## 🚀 快速开始

### 前提条件

- Python 3.13+
- GCP 项目并启用相关 API
- Telegram Bot Token
- GCS Bucket

### 本地开发

```bash
# 1. 克隆仓库
git clone https://github.com/Winson-030/2026-monitor-agent.git
cd gcp-monitoring-agent

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或: venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的配置

# 5. 运行
python main.py
```

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/run-inspection` | POST | 执行巡检任务 |
| `/telegram-webhook` | POST | Telegram Webhook |
| `/healthz` | GET | 健康检查 |

---

## 📦 部署到 Cloud Run

### 1. 准备 GCP 项目

```bash
# 设置项目
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# 启用 API
gcloud services enable run.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 2. 创建 GCS Bucket

```bash
gcloud storage buckets create gs://$PROJECT_ID-inspection --location=us-central1
```

### 3. 构建并部署

```bash
# 构建镜像
gcloud builds submit --tag gcr.io/$PROJECT_ID/gcp-monitor

# 部署到 Cloud Run
gcloud run deploy gcp-monitor \
  --image gcr.io/$PROJECT_ID/gcp-monitor \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="TELEGRAM_BOT_TOKEN=your-bot-token" \
  --set-env-vars="TELEGRAM_CHAT_ID=your-chat-id"
```

### 4. 配置 Cloud Scheduler

```bash
# 创建每 5 分钟执行一次的调度器
gcloud scheduler jobs create http gcp-monitor-job \
  --schedule="*/5 * * * *" \
  --uri="https://your-service-url/run-inspection" \
  --http-method=POST \
  --location=us-central1
```

详细部署步骤请参见 [DEPLOYMENT.md](DEPLOYMENT.md)。

---

## ⚙️ 配置说明

### config.yaml

```yaml
gcp:
  project_id: "your-project-id"      # GCP 项目 ID
  region: "us-central1"              # 默认区域
  default_zone: "us-central1-a"      # 默认可用区

thresholds:
  cpu_critical: 90                   # CPU 危急阈值 (%)
  cpu_warning: 80                    # CPU 警告阈值 (%)
  disk_critical: 90                  # 磁盘危急阈值 (%)
  disk_warning: 80                   # 磁盘警告阈值 (%)

gcs_bucket: "your-bucket-name"       # GCS Bucket 名称

budget:
  daily_max_usd: 3.0                 # 每日预算上限 (USD)

inspection:
  zones:                             # 巡检区域列表
    - "us-central1-a"
    - "us-central1-b"
```

### 环境变量

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram Bot Token (@BotFather 获取) |
| `TELEGRAM_CHAT_ID` | ✅ | Telegram 聊天 ID |
| `GOOGLE_APPLICATION_CREDENTIALS` | - | GCP 服务账号密钥路径（本地开发） |

详细配置说明请参见 [CONFIGURATION.md](CONFIGURATION.md)。

---

## 💬 Telegram Bot 命令

| 命令 | 说明 |
|------|------|
| `/status` | 查看最新的巡检报告 |
| `/inspect <实例名>` | 查看指定实例的详细分析 |
| 任意文字 | 智能问答（基于最新报告） |

---

## 📁 项目结构

```
gcp-monitoring-agent/
├── agents/                 # AI 分析模块
│   ├── __init__.py
│   ├── inspector.py       # Gemini 分析器
│   └── prompts.py         # 系统提示词
├── fetcher/               # 数据采集模块
│   ├── __init__.py
│   └── metrics.py         # GCP 指标获取
├── notify/                # 通知模块
│   ├── __init__.py
│   └── telegram.py        # Telegram Bot
├── store/                 # 存储模块
│   ├── __init__.py
│   └── state_manager.py   # GCS 状态管理
├── main.py                # Flask 应用入口
├── orchestrator.py        # 巡检流程编排
├── config.yaml            # 配置文件
├── requirements.txt       # Python 依赖
├── Dockerfile             # 容器镜像
├── .env.example           # 环境变量示例
├── README.md              # 项目文档
├── DEPLOYMENT.md          # 部署文档
└── CONFIGURATION.md       # 配置文档
```

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. **Fork** 本仓库
2. 创建你的 **Feature Branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit** 你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. **Push** 到分支 (`git push origin feature/AmazingFeature`)
5. 打开 **Pull Request**

### 贡献者

<a href="https://github.com/Winson-030/2026-monitor-agent/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Winson-030/2026-monitor-agent" alt="Contributors" />
</a>

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

---

## 🔗 相关链接

- [GCP Cloud Run 文档](https://cloud.google.com/run/docs)
- [Gemini API 文档](https://ai.google.dev/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/Winson-030">Winson</a>
</p>

---

<h2 id="english">🇺🇸 English</h2>

## 📋 Project Overview

**GCP Monitoring Agent** is an intelligent GCP resource inspection system deployed on Cloud Run. It periodically collects GCE instance metrics, analyzes them using Gemini 2.5 Flash AI, and sends alerts via Telegram Bot.

### Key Features

- 🤖 **AI-Powered Analysis** - Smart metric analysis with Gemini 2.5 Flash
- 📊 **Automatic Metrics Collection** - Deterministic data collection based on GCP Monitoring API
- 💬 **Telegram Integration** - Bot interaction with `/status`, `/inspect` commands
- ☁️ **Cloud Run Deployment** - Serverless architecture with pay-per-use
- 📁 **State Persistence** - Inspection reports stored in GCS
- 🔧 **Flexible Configuration** - YAML config + environment variables

---

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- GCP project with APIs enabled
- Telegram Bot Token
- GCS Bucket

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/Winson-030/2026-monitor-agent.git
cd gcp-monitoring-agent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your configuration

# 5. Run
python main.py
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/run-inspection` | POST | Run inspection job |
| `/telegram-webhook` | POST | Telegram Webhook |
| `/healthz` | GET | Health check |

---

## 📦 Deploy to Cloud Run

### 1. Prepare GCP Project

```bash
# Set project
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 2. Build and Deploy

```bash
# Build image
gcloud builds submit --tag gcr.io/$PROJECT_ID/gcp-monitor

# Deploy to Cloud Run
gcloud run deploy gcp-monitor \
  --image gcr.io/$PROJECT_ID/gcp-monitor \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="TELEGRAM_BOT_TOKEN=your-bot-token" \
  --set-env-vars="TELEGRAM_CHAT_ID=your-chat-id"
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment steps.

---

## ⚙️ Configuration

### config.yaml

```yaml
gcp:
  project_id: "your-project-id"      # GCP Project ID
  region: "us-central1"              # Default region
  default_zone: "us-central1-a"      # Default zone

thresholds:
  cpu_critical: 90                   # CPU critical threshold (%)
  cpu_warning: 80                    # CPU warning threshold (%)
  disk_critical: 90                  # Disk critical threshold (%)
  disk_warning: 80                   # Disk warning threshold (%)

gcs_bucket: "your-bucket-name"       # GCS Bucket name

budget:
  daily_max_usd: 3.0                 # Daily budget limit (USD)

inspection:
  zones:                             # Zones to inspect
    - "us-central1-a"
    - "us-central1-b"
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram Bot Token (from @BotFather) |
| `TELEGRAM_CHAT_ID` | ✅ | Telegram Chat ID |
| `GOOGLE_APPLICATION_CREDENTIALS` | - | GCP service account key path (local dev) |

See [CONFIGURATION.md](CONFIGURATION.md) for detailed configuration.

---

## 💬 Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/status` | View latest inspection report |
| `/inspect <instance>` | View detailed analysis for specific instance |
| Any text | Smart Q&A based on latest report |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/Winson-030">Winson</a>
</p>
