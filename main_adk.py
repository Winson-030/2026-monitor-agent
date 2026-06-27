"""
ADK-based web chat interface for GCP Monitoring Agent.

Provides FastAPI application with:
- ADK API endpoints for agent interaction
- Optional ADK web UI for browser-based chat
- Health check endpoint

Run locally:
    adk web --port 8000

Run for production (Cloud Run):
    uvicorn main_adk:app --host 0.0.0.0 --port $PORT
"""

import os
import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

# Get the directory containing this file
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Session storage (SQLite for lightweight persistent sessions)
SESSION_SERVICE_URI = os.getenv(
    "ADK_SESSION_URI",
    "sqlite+aiosqlite:///./sessions.db",
)

# CORS: allow web UI to connect
ALLOWED_ORIGINS = os.getenv(
    "ADK_ALLOWED_ORIGINS",
    "http://localhost:8000,http://localhost:4200",
).split(",")

# Whether to serve the ADK web UI alongside the API
SERVE_WEB_INTERFACE = os.getenv("ADK_SERVE_WEB", "true").lower() == "true"

# Create the FastAPI app from ADK
app: FastAPI = get_fast_api_app(
    agents_dir=os.path.join(AGENT_DIR, "agents"),
    session_service_uri=SESSION_SERVICE_URI,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)


# Add a health check endpoint
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "gcp-monitor-adk",
        "agents": ["gcp_monitor_agent"],
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
