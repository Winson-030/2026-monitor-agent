# 配置指南

> ⚠️ **本文档为快速参考。完整配置指南请参阅 [English Version](CONFIGURATION_en.md)**

---

## 📄 配置文件

### config.yaml

```yaml
gcp:
  project_id: "your-project-id"
  region: "us-central1"
  default_zone: "us-central1-a"

thresholds:
  cpu_critical: 90
  cpu_warning: 80
  disk_critical: 90
  disk_warning: 80

gcs_bucket: "your-bucket-name"

budget:
  daily_max_usd: 3.0

inspection:
  zones:
    - "us-central1-a"
```

## 🔐 环境变量

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | ✅ | Telegram 聊天 ID |
| `GOOGLE_CLOUD_PROJECT` | - | GCP 项目 ID |

## 📊 阈值推荐

| 环境 | CPU 警告 | CPU 危急 | 磁盘警告 | 磁盘危急 |
|------|----------|----------|----------|----------|
| 开发环境 | 70% | 85% | 80% | 90% |
| 生产环境 | 80% | 90% | 80% | 90% |
| 高负载 | 85% | 95% | 85% | 95% |

## 📚 完整文档

- [完整配置指南 (English)](CONFIGURATION_en.md)
- [部署指南 (English)](DEPLOYMENT_en.md)
- [主文档 (English)](../README.md)
