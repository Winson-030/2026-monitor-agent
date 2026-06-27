import yaml
from flask import Flask, request
from orchestrator import InspectionLoop
from notify.telegram import TelegramHandler, format_report, format_alert

def load_config(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)

config = load_config()
loop = InspectionLoop(config["gcp"]["project_id"], config)
tg = TelegramHandler(
    token=config["telegram"]["bot_token"],
    chat_id=config["telegram"]["chat_id"],
)

app = Flask(__name__)


@app.route("/run-inspection", methods=["POST"])
def run_inspection():
    zone = request.json.get("zone", config["gcp"]["default_zone"])
    report = loop.run(zone=zone)

    findings = [
        r for r in report["results"]
        if r.get("analysis", {}).get("status") in ("critical", "warning")
    ]
    if findings:
        tg.send_alert(format_alert(findings))

    return {"status": "ok", "targets": len(report["results"])}


@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    data = request.get_json()
    tg.handle_webhook(data, loop)
    return {"ok": True}


@app.route("/healthz")
def healthz():
    return {"status": "ok"}
