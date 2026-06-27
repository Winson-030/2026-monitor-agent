# GCP Monitoring Agent

GCP 巡检 Agent - 部署到 Cloud Run，定时拉取指标 → Gemini Flash 分析 → Telegram 告警推送。

## 架构

- **MetricsFetcher**: GCP Monitoring API 确定性采集 (CPU/磁盘/状态)
- **Inspector**: Gemini 2.5 Flash LLM 分析指标
- **GCSStateManager**: GCS 单文件持久化巡检报告
- **TelegramHandler**: Bot API 交互 (/status, /inspect)

## 部署

```bash
# 构建并部署到 Cloud Run
gcloud builds submit --tag gcr.io/$PROJECT/gcp-monitor
gcloud run deploy gcp-monitor --image gcr.io/$PROJECT/gcp-monitor --region us-central1
```

## 本地开发

```bash
pip install -r requirements.txt
python main.py
```

## 配置

编辑 `config.yaml`：
- GCP project ID
- Telegram bot token
- GCS bucket 名称
- 告警阈值
