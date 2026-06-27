import json
from datetime import datetime
from google.cloud import storage

class GCSStateManager:
    STATE_FILE = "inspection/latest_report.json"

    def __init__(self, bucket: str):
        self.bucket = storage.Client().bucket(bucket)
        self.blob = self.bucket.blob(self.STATE_FILE)

    def save(self, report: dict):
        report["updated_at"] = datetime.utcnow().isoformat()
        self.blob.upload_from_string(json.dumps(report, indent=2))

    def load(self) -> dict | None:
        if not self.blob.exists():
            return None
        return json.loads(self.blob.download_as_string())

    # ── Alert persistence ───────────────────────────────
    ALERTS_FILE = "alerts/active_alerts.json"

    def _init_alerts_blob(self):
        self.alerts_blob = self.bucket.blob(self.ALERTS_FILE)

    def save_alerts(self, alerts: list[dict]):
        """Persist active alerts to GCS."""
        payload = {
            "alerts": alerts,
            "updated_at": datetime.utcnow().isoformat(),
        }
        self.alerts_blob.upload_from_string(json.dumps(payload, indent=2))

    def load_alerts(self) -> dict | None:
        """Load active alerts from GCS."""
        if not hasattr(self, "alerts_blob"):
            self._init_alerts_blob()
        if not self.alerts_blob.exists():
            return None
        return json.loads(self.alerts_blob.download_as_string())
