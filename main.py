import os
import yaml
import traceback
from flask import Flask, request

app = Flask(__name__)

# Lazy initialization to handle startup errors gracefully
_config = None
_loop = None
_tg = None

def get_config():
    global _config
    if _config is None:
        config_path = os.getenv("CONFIG_PATH", "config.yaml")
        with open(config_path) as f:
            _config = yaml.safe_load(f)
    return _config

def get_loop():
    global _loop
    if _loop is None:
        from orchestrator import InspectionLoop
        config = get_config()
        _loop = InspectionLoop(config["gcp"]["project_id"], config)
    return _loop

def get_tg():
    global _tg
    if _tg is None:
        from notify.telegram import TelegramHandler
        _tg = TelegramHandler(
            token=os.getenv("TELEGRAM_BOT_TOKEN"),
            chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        )
    return _tg


from notify.telegram import format_report, format_alert

@app.route("/run-inspection", methods=["POST"])
def run_inspection():
    try:
        config = get_config()
        loop = get_loop()
        tg = get_tg()
        zone = request.json.get("zone", config["gcp"]["default_zone"]) if request.is_json else config["gcp"]["default_zone"]
        report = loop.run(zone=zone)

        findings = [
            r for r in report["results"]
            if r.get("analysis", {}).get("status") in ("critical", "warning")
        ]
        if findings:
            tg.send_alert(format_alert(findings))

        return {"status": "ok", "targets": len(report["results"])}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    try:
        data = request.get_json()
        tg = get_tg()
        loop = get_loop()
        tg.handle_webhook(data, loop)
        return {"ok": True}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}


@app.route("/")
def root():
    return {"status": "ok", "message": "GCP Monitoring Agent is running"}

@app.route("/health")
def health():
    return {"status": "ok"}
