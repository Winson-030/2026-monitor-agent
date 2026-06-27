# GCP Monitoring Agent

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?logo=python" alt="Python 3.13">
  <img src="https://img.shields.io/badge/Cloud%20Run-GCP-orange?logo=google-cloud" alt="Cloud Run">
  <img src="https://img.shields.io/badge/Gemini-2.5%20Flash-green?logo=google" alt="Gemini 2.5 Flash">
  <img src="https://img.shields.io/badge/License-MIT-blue" alt="License: MIT">
</p>

> ⚠️ **本文档为快速参考，完整文档请参见 [English Version](README.md)**

---

## 📋 项目简介

**GCP Monitoring Agent** 是一个智能的 GCP 资源巡检系统，部署于 Cloud Run，能够定时采集 GCE 实例指标，通过 Gemini 2.5 Flash AI 进行分析，并通过 Telegram Bot 推送告警。

## ✨ 核心特性

- 🤖 **AI 驱动分析** - 使用 Gemini 2.5 Flash 智能分析监控指标
- 📊 **自动指标采集** - 基于 GCP Monitoring API 的确定性数据采集
- 💬 **Telegram 集成** - Bot 交互支持 (`/status`, `/inspect` 命令)
- ☁️ **Cloud Run 部署** - 无服务器架构，按需付费
- 📁 **状态持久化** - GCS 存储巡检报告

## 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/Winson-030/2026-monitor-agent.git
cd gcp-monitoring-agent

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置并运行
cp .env.example .env
# 编辑 .env 文件
python main.py
```

## 💬 Telegram 命令

| 命令 | 说明 |
|------|------|
| `/status` | 查看最新巡检报告 |
| `/inspect <实例名>` | 查看指定实例的详细分析 |

## 💰 成本估算

| 项目 | 月费用 |
|------|--------|
| Cloud Run | ~$5-8 |
| Cloud Scheduler | ~$0.50 |
| Gemini Flash API | ~$0.30 |
| **合计** | **~$6-9/月** |

## 📚 完整文档

| 文档 | 链接 |
|------|------|
| **完整 README** | [English Version](README.md) |
| **部署指南** | [DEPLOYMENT_en.md](DEPLOYMENT_en.md) |
| **配置指南** | [CONFIGURATION_en.md](CONFIGURATION_en.md) |

## 📄 许可证

[MIT License](LICENSE)

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/Winson-030">Winson</a>
</p>
