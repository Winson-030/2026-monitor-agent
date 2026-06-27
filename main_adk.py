"""
ADK web chat interface for GCP Monitoring Agent.

Uses get_fast_api_app() to create a FastAPI application with:
- ADK API endpoints /list-apps, /run_sse
- Optional ADK web UI for browser-based chat
- Health check endpoint

Run locally:
    adk web --port 8000

Run for production:
    uvicorn main_adk:app --host 0.0.0.0 --port $PORT
"""

import os
import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

AGENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents")
SESSION_SERVICE_URI = os.getenv("ADK_SESSION_URI", "sqlite+aiosqlite:///./sessions.db")
ALLOWED_ORIGINS = os.getenv("ADK_ALLOWED_ORIGINS", "http://localhost:8000,http://localhost:4200").split(",")
SERVE_WEB = os.getenv("ADK_SERVE_WEB", "true").lower() == "true"

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_SERVICE_URI,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB,
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gcp-monitor-adk", "agent": "gcp_monitor_agent"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
