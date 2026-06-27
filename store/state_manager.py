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
