"""
GCP Monitoring Agent — FastAPI + ADK Web Chat Interface.

Combines:
- ADK web chat UI at /
- Existing inspection and Telegram endpoints at /run-inspection, /telegram-webhook

Deployed on Cloud Run:
    https://gcp-monitor-agent-102942669966.us-central1.run.app
"""

import os
import json
import yaml
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from google.adk.cli.fast_api import get_fast_api_app

# ── ADK Setup ─────────────────────────────────────────────
AGENTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents")
SESSION_URI = os.getenv("ADK_SESSION_URI", "sqlite+aiosqlite:///./sessions.db")
ALLOWED_ORIGINS = os.getenv("ADK_ALLOWED_ORIGINS", "*").split(",")

app: FastAPI = get_fast_api_app(
    agents_dir=AGENTS_DIR,
    session_service_uri=SESSION_URI,
    allow_origins=ALLOWED_ORIGINS,
    web=True,
)

# ── Lazy Initialization ───────────────────────────────────
_config_cache = None


def get_config() -> dict:
    global _config_cache
    if _config_cache is None:
        config_path = os.getenv("CONFIG_PATH", "config.yaml")
        with open(config_path) as f:
            _config_cache = yaml.safe_load(f)
    return _config_cache


def get_telegram_handler(token: str, chat_id: str):
    from notify.telegram import TelegramHandler
    return TelegramHandler(token=token, chat_id=chat_id)


def get_inspection_loop(project_id: str, config: dict, mode: str = "standard"):
    from orchestrator import InspectionLoop
    return InspectionLoop(project_id, config, mode=mode)


# ── Existing Endpoints (converted from Flask) ─────────────

@app.post("/run-inspection")
async def run_inspection(request: Request):
    """Cloud Scheduler 定时触发：采集指标 → AI 分析 → 发送告警"""
    try:
        config = get_config()
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
        zone = body.get("zone", config["gcp"]["default_zone"])
        mode = body.get("mode", "standard")

        loop = get_inspection_loop(config["gcp"]["project_id"], config, mode=mode)
        tg = get_telegram_handler(
            token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        )

        report = loop.run(zone=zone)

        findings = [
            r for r in report["results"]
            if r.get("analysis", {}).get("status") in ("critical", "warning")
        ]
        if findings:
            from notify.telegram import format_alert
            tg.send_alert(format_alert(findings))

        return {"status": "ok", "mode": mode, "targets": len(report["results"])}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    """Telegram Bot webhook：接收用户消息并回复"""
    try:
        body = await request.json()
        tg = get_telegram_handler(
            token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        )
        config = get_config()
        loop = get_inspection_loop(config["gcp"]["project_id"], config)
        tg.handle_webhook(body, loop)
        return {"ok": True}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "gcp-monitor-agent",
        "mode": "adk-web",
        "agent": "gcp_monitor_agent",
    }
