# Changelog

## [v14] - 2026-06-27

### Features
- **Background VM Alert Watcher**: Real-time 60-second polling loop for automatic VM alerting
  - `scheduler.py`: New `BackgroundWatcher` class with continuous monitoring
  - Checks CPU and disk metrics against configurable thresholds (80% warning, 90% critical)
  - In-memory alert cache for fast ADK tool access
  - GCS persistence (`alerts/active_alerts.json`) for Cloud Run restart survivability
  - Alert lifecycle: auto-create on breach, auto-clear on recovery
- **`get_active_alerts()` ADK Tool**: New tool on the ADK agent exposing current alert state
  - Returns sorted alerts (critical first, then by time)
  - Integrates with web chat: "现在有没有告警？" auto-triggers this tool
  - Agent auto-checks alerts at conversation start

### Changes
- **Flask to FastAPI Migration**: Unified all endpoints under FastAPI for ADK compatibility
  - `main.py` now uses FastAPI instead of Flask
  - Supports both Telegram webhook and ADK web UI from same process
  - Health endpoint at `/health`
- **Dockerfile**: Added gcloud CLI installation for `run_gcloud_query` tool
  - Installs `google-cloud-cli` via apt
  - Enables arbitrary read-only GCP queries from the ADK agent

### Technical
- `scheduler.py` module-level singleton pattern (`get_watcher()`, `create_watcher()`)
- Alert deduplication by `zone:vm:trigger` key
- Thread-safe async design with `asyncio.create_task`
- GCS alert persistence with init-on-startup restoration

---

## [v13] - 2026-06-27

### Fixes
- **ADK Import Error**: Remove ADK import from `agents/__init__.py` to prevent startup error
  - Flask app doesn't require ADK dependencies
  - ADK agent available separately via `agents/agent.py`

---

## [v12] - 2026-06-27

### Features
- **ADK Web Chat Interface**: Consolidated ADK agent into `agents/agent.py`
  - 6 monitoring tools: list_vm_instances, get_vm_metrics, get_latest_report, run_gcloud_query, get_active_alerts, query_report
  - FastAPI entry point: `main_adk.py`
  - Web UI via `adk web` command
- **Config Module**: Dataclass-based YAML config loader (`config.py`)
  - Type-safe configuration from `config.yaml`
  - Supports environment variable overrides

### Changes
- Restructured project to support both Telegram and ADK Web Chat
- Removed separate `agents/adk_agent/` directory
- Updated documentation

---

## [v11] - 2026-06-27

### Features
- **Natural Language GCP Queries**: Ask questions in Chinese/English and get real-time GCP resource data
  - `query/intent.py`: LLM-based intent recognition using Gemini 2.5 Flash
  - `query/executor.py`: Real-time VM queries using Google Cloud Python SDK
  - Supported query types: vm_count, vm_list, vm_status, zone_count, resource_summary, vm_metrics
  - Automatic fallback to LLM chat for unrecognized or complex queries
  - Integrated with Telegram webhook handler

### Technical
- Intent recognition with structured JSON output (`QueryIntent` dataclass)
- Uses `google-cloud-compute` Python client for real-time data
- MarkdownV2 formatted responses with tables and emoji

---

## [v10] - 2026-06-27

### Features
- **Telegram MarkdownV2 Support**: Add proper Markdown formatting for all messages
  - `escape_markdown()`: Escape Telegram MarkdownV2 special characters
  - `send_message()`: Support parse_mode with automatic fallback to plain text
  - `format_report()`: Format reports as Markdown tables with headers
  - `format_analysis()`: Format analysis with Markdown emphasis
  - `format_alert()`: Format alerts with Markdown and emoji
  - `answer_question()`: Format QA responses with Markdown
  - `/help` command: Display help with formatted command list

### Technical
- All messages use `parse_mode="MarkdownV2"` by default
- Automatic fallback to plain text if MarkdownV2 parsing fails
- VM names and reasons are properly escaped to prevent parsing errors

---

## [v1-v9] - 2026-06-27

Initial MVP implementation:

### Features
- GCP Monitoring API integration for metric collection
- Gemini 2.5 Flash AI-powered metric analysis
- Flask web application for Telegram webhook handling
- Cloud Scheduler for periodic inspection triggers
- GCS state persistence for inspection reports
- Multi-model support (Gemini 2.5 Flash + 3.1 Pro)
- Natural language chat with topic boundaries
- Support for Chinese and English queries
- Comprehensive documentation (English, Chinese, Japanese)
