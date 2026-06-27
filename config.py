"""Configuration loader for GCP Monitoring Agent."""

import yaml
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GCPConfig:
    project_id: str
    region: str
    default_zone: str


@dataclass
class ThresholdsConfig:
    cpu_critical: int
    cpu_warning: int
    disk_critical: int
    disk_warning: int


@dataclass
class Config:
    gcp: GCPConfig
    gcs_bucket: str
    thresholds: ThresholdsConfig
    budget: dict
    inspection: dict


def load_config() -> Config:
    """Load configuration from config.yaml."""
    config_path = Path(__file__).parent / "config.yaml"
    
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    gcp_data = data.get('gcp', {})
    thresholds_data = data.get('thresholds', {})
    
    return Config(
        gcp=GCPConfig(
            project_id=gcp_data.get('project_id', ''),
            region=gcp_data.get('region', ''),
            default_zone=gcp_data.get('default_zone', '')
        ),
        gcs_bucket=data.get('gcs_bucket', ''),
        thresholds=ThresholdsConfig(
            cpu_critical=thresholds_data.get('cpu_critical', 90),
            cpu_warning=thresholds_data.get('cpu_warning', 80),
            disk_critical=thresholds_data.get('disk_critical', 90),
            disk_warning=thresholds_data.get('disk_warning', 80)
        ),
        budget=data.get('budget', {}),
        inspection=data.get('inspection', {})
    )


# Global config instance
config = load_config()
