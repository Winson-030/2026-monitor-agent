# 設定ガイド

> ⚠️ **本文档为快速参考。完全な設定ガイドは [English Version](CONFIGURATION_en.md) を参照してください**

---

## 📄 設定ファイル

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

## 🔐 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | ✅ | Telegram チャット ID |
| `GOOGLE_CLOUD_PROJECT` | - | GCP プロジェクト ID |

## 📊 しきい値の推奨値

| 環境 | CPU 警告 | CPU クリティカル | ディスク警告 | ディスククリティカル |
|------|----------|------------------|--------------|----------------------|
| 開発環境 | 70% | 85% | 80% | 90% |
| 本番環境 | 80% | 90% | 80% | 90% |
| 高負荷 | 85% | 95% | 85% | 95% |

## 📚 完全なドキュメント

- [完全な設定ガイド (English)](CONFIGURATION_en.md)
- [デプロイガイド (English)](DEPLOYMENT_en.md)
- [メインドキュメント (English)](../README.md)
