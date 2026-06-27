import time
from google.cloud import monitoring_v3
import google.cloud.compute_v1 as compute_v1

class MetricsFetcher:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.monitoring = monitoring_v3.MetricServiceClient()
        self.compute = compute_v1.InstancesClient()

    def fetch(self, zone: str = "us-central1-a") -> list[dict]:
        instances = self.compute.list(project=self.project_id, zone=zone)
        results = []

        for instance in instances:
            results.append({
                "id": instance.name,
                "cpu": self._query_cpu(instance.id),
                "memory": None,
                "disk": self._query_disk_usage(instance.id),
                "status": instance.status,
                "zone": zone,
            })

        return results

    def fetch_for_target(self, target: str, zone: str = "us-central1-a") -> dict | None:
        instances = self.compute.list(project=self.project_id, zone=zone)
        for instance in instances:
            if instance.name == target:
                return {
                    "id": instance.name,
                    "cpu": self._query_cpu(instance.id),
                    "memory": None,
                    "disk": self._query_disk_usage(instance.id),
                    "status": instance.status,
                    "zone": zone,
                }
        return None

    def _query_cpu(self, instance_id: int) -> float | None:
        now = time.time()
        request = monitoring_v3.ListTimeSeriesRequest(
            name=f"projects/{self.project_id}",
            filter=(
                'metric.type="compute.googleapis.com/instance/cpu/utilization" '
                f'AND resource.labels.instance_id="{instance_id}"'
            ),
            interval={
                "start_time": {"seconds": int(now) - 180},
                "end_time": {"seconds": int(now)},
            },
            aggregation={
                "alignment_period": {"seconds": 60},
                "per_series_aligner": "ALIGN_P99",
            },
        )
        series = list(self.monitoring.list_time_series(request))
        if not series or not series[0].points:
            return None
        return series[0].points[-1].value.double_value * 100

    def _query_disk_usage(self, instance_id: int) -> float | None:
        return None
