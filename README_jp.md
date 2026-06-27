# GCP Monitoring Agent

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?logo=python" alt="Python 3.13">
  <img src="https://img.shields.io/badge/Cloud%20Run-GCP-orange?logo=google-cloud" alt="Cloud Run">
  <img src="https://img.shields.io/badge/Gemini-2.5%20Flash-green?logo=google" alt="Gemini 2.5 Flash">
  <img src="https://img.shields.io/badge/License-MIT-blue" alt="License: MIT">
</p>

> ⚠️ **本文档为快速参考。完整文档请参阅 [English Version](README.md)**

---

## 📋 プロジェクト概要

**GCP Monitoring Agent** は、Cloud Run 上にデプロイされるインテリジェントな GCP リソース監査システムです。定期的に GCE インスタンスのメトリクスを収集し、Gemini 2.5 Flash AI を用いて分析を行い、Telegram Bot 経由でアラートを通知します。

## ✨ 主な機能

- 🤖 **AI 駆動型分析** - Gemini 2.5 Flash を使用したインテリジェント分析
- 📊 **自動メトリクス収集** - GCP Monitoring API に基づくデータ収集
- 💬 **Telegram 連携** - Bot とのインタラクション対応 (`/status`, `/inspect` コマンド)
- ☁️ **Cloud Run デプロイ** - サーバーレスアーキテクチャによる従量課金制
- 📁 **状態の永続化** - 監査レポートを GCS に保存

## 🚀 クイックスタート

```bash
# 1. リポジトリをクローン
git clone https://github.com/Winson-030/2026-monitor-agent.git
cd gcp-monitoring-agent

# 2. 依存関係をインストール
pip install -r requirements.txt

# 3. 設定して実行
cp .env.example .env
# .env を編集
python main.py
```

## 💬 Telegram コマンド

| コマンド | 説明 |
|---------|------|
| `/status` | 最新の監査レポートを表示 |
| `/inspect <インスタンス>` | 特定インスタンスの詳細分析を表示 |

## 💰 コスト見積もり

| 項目 | 月額費用 |
|------|----------|
| Cloud Run | ~$5-8 |
| Cloud Scheduler | ~$0.50 |
| Gemini Flash API | ~$0.30 |
| **合計** | **~$6-9/月** |

## 📚 完全なドキュメント

| ドキュメント | リンク |
|-------------|--------|
| **完全版 README** | [English Version](README.md) |
| **デプロイガイド** | [DEPLOYMENT_en.md](DEPLOYMENT_en.md) |
| **設定ガイド** | [CONFIGURATION_en.md](CONFIGURATION_en.md) |

## 📄 ライセンス

[MIT License](LICENSE)

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/Winson-030">Winson</a>
</p>
