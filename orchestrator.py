from datetime import datetime
from fetcher.metrics import MetricsFetcher
from agents.inspector import Inspector
from store.state_manager import GCSStateManager

class InspectionLoop:
    def __init__(self, project_id: str, config: dict):
        self.project_id = project_id
        self.config = config
        self.fetcher = MetricsFetcher(project_id)
        self.inspector = Inspector()
        self.state = GCSStateManager(config["gcs_bucket"])

    def run(self, zone: str = "us-central1-a") -> dict:
        raw = self.fetcher.fetch(zone)

        results = []
        for r in raw:
            try:
                analysis = self.inspector.analyze(r["id"], r)
            except Exception as e:
                analysis = {"status": "error", "reason": str(e)}
            results.append({**r, "analysis": analysis})

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "zone": zone,
            "results": results,
        }
        self.state.save(report)
        return report

    def get_latest_report(self) -> dict | None:
        return self.state.load()
