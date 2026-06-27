"""Background metrics watcher — polls VM metrics every 60s and raises alerts."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fetcher.metrics import MetricsFetcher
from store.state_manager import GCSStateManager

logger = logging.getLogger(__name__)

THRESHOLDS = {
    "cpu_critical": 90.0,
    "cpu_warning": 80.0,
    "disk_critical": 90.0,
    "disk_warning": 80.0,
}

class BackgroundWatcher:
    """Periodically fetches VM metrics and maintains an alert list.

    Alerts are stored:
    - In-memory (for fast ADK tool access)
    - In GCS (for persistence across Cloud Run restarts)
    """

    def __init__(self, project_id: str, bucket: str, zones: list[str], interval_sec: int = 60):
        self.project_id = project_id
        self.bucket_name = bucket
        self.zones = zones
        self.interval = interval_sec
        self.fetcher: Optional[MetricsFetcher] = None
        self.state: Optional[GCSStateManager] = None
        self._alerts: dict[str, dict] = {}  # key = "zone:vm:trigger"
        self._task: Optional[asyncio.Task] = None

    # ── Public API ────────────────────────────────────

    def get_alerts(self) -> list[dict]:
        """Return current active alerts, sorted by severity then time."""
        sorted_alerts = sorted(
            self._alerts.values(),
            key=lambda a: (0 if a["level"] == "critical" else 1, a["since"]),
        )
        return sorted_alerts

    async def start(self):
        """Start the background polling loop."""
        if self._task is not None:
            return
        self.fetcher = MetricsFetcher(self.project_id)
        self.state = GCSStateManager(self.bucket_name)
        self.state.ALERTS_FILE = "alerts/active_alerts.json"
        self.state._init_alerts_blob()
        self._restore_from_gcs()
        self._task = asyncio.create_task(self._loop())
        logger.info("BackgroundWatcher started (interval=%ss, zones=%s)",
                     self.interval, self.zones)

    async def stop(self):
        """Stop the background polling loop."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("BackgroundWatcher stopped")

    # ── Internal ───────────────────────────────────────

    async def _loop(self):
        while True:
            try:
                await self._poll_once()
            except Exception as e:
                logger.exception("Watcher poll error: %s", e)
            await asyncio.sleep(self.interval)

    async def _poll_once(self):
        """Scan all RUNNING VMs across zones, check thresholds, update alerts."""
        new_alerts: dict[str, dict] = {}

        for zone in self.zones:
            try:
                instances = self.fetcher.compute.list(
                    project=self.project_id, zone=zone
                )
            except Exception as e:
                logger.warning("Failed to list instances in %s: %s", zone, e)
                continue

            for inst in instances:
                if inst.status != "RUNNING":
                    continue

                try:
                    metrics = self.fetcher.fetch_for_target(inst.name, zone)
                except Exception as e:
                    logger.warning("Failed to fetch metrics for %s: %s", inst.name, e)
                    continue

                if metrics is None:
                    continue

                self._check_thresholds(new_alerts, inst.name, zone, metrics)

        # Clear alerts for VMs that recovered
        recovered = set(self._alerts.keys()) - set(new_alerts.keys())
        for key in recovered:
            a = self._alerts.pop(key)
            logger.info("Alert cleared: %s / %s (was %s)", a["vm"], a["trigger"], a["level"])

        # Merge in new/updated alerts
        for key, alert in new_alerts.items():
            self._alerts[key] = alert

        # Persist to GCS
        self._save_to_gcs()

    def _check_thresholds(self, alerts: dict, vm: str, zone: str, metrics: dict):
        """Evaluate metrics against thresholds and build alerts."""
        now = datetime.now(timezone.utc).isoformat()

        # CPU
        cpu = metrics.get("cpu")
        if isinstance(cpu, (int, float)):
            if cpu >= THRESHOLDS["cpu_critical"]:
                key = f"{zone}:{vm}:cpu"
                alerts[key] = self._build_alert(key, vm, zone, "cpu", cpu, "critical", now)
            elif cpu >= THRESHOLDS["cpu_warning"]:
                key = f"{zone}:{vm}:cpu"
                alerts[key] = self._build_alert(key, vm, zone, "cpu", cpu, "warning", now)

        # Disk
        disk = metrics.get("disk")
        if isinstance(disk, (int, float)):
            if disk >= THRESHOLDS["disk_critical"]:
                key = f"{zone}:{vm}:disk"
                alerts[key] = self._build_alert(key, vm, zone, "disk", disk, "critical", now)
            elif disk >= THRESHOLDS["disk_warning"]:
                key = f"{zone}:{vm}:disk"
                alerts[key] = self._build_alert(key, vm, zone, "disk", disk, "warning", now)

    def _build_alert(self, key: str, vm: str, zone: str, trigger: str,
                     value: float, level: str, now: str) -> dict:
        """Create or update an alert dict."""
        existing = self._alerts.get(key)
        return {
            "vm": vm,
            "zone": zone,
            "trigger": trigger,
            "value": round(value, 1),
            "threshold": THRESHOLDS.get(f"{trigger}_{level}", 80),
            "level": level,
            "since": existing["since"] if existing else now,
            "last_updated": now,
        }

    # ── GCS persistence ────────────────────────────────

    def _restore_from_gcs(self):
        """Load alerts from GCS on startup (survive Cloud Run restarts)."""
        try:
            data = self.state.load_alerts()
            if data and data.get("alerts"):
                for a in data["alerts"]:
                    key = f"{a['zone']}:{a['vm']}:{a['trigger']}"
                    self._alerts[key] = a
                logger.info("Restored %d alerts from GCS", len(self._alerts))
        except Exception as e:
            logger.warning("Failed to restore alerts from GCS: %s", e)

    def _save_to_gcs(self):
        """Persist current alerts to GCS."""
        try:
            self.state.save_alerts(list(self._alerts.values()))
        except Exception as e:
            logger.warning("Failed to persist alerts to GCS: %s", e)


# ── Module-level singleton ────────────────────────────────
_watcher: Optional[BackgroundWatcher] = None


def get_watcher() -> Optional[BackgroundWatcher]:
    return _watcher


def create_watcher(project_id: str, bucket: str, zones: list[str],
                   interval_sec: int = 60) -> BackgroundWatcher:
    global _watcher
    _watcher = BackgroundWatcher(project_id, bucket, zones, interval_sec)
    return _watcher
