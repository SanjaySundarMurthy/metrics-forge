"""Export reporter for YAML, JSON output."""

import json
from pathlib import Path

import yaml

from ..models import ForgeOutput, GrafanaDashboard


def export_prometheus_rules(output: ForgeOutput, filepath: str) -> str:
    """Export Prometheus alert rules as YAML."""
    data = {
        "groups": [g.to_prometheus() for g in output.alert_groups]
    }
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False), encoding='utf-8')
    return str(path)


def export_grafana_dashboards(dashboards: list[GrafanaDashboard], output_dir: str) -> list[str]:
    """Export Grafana dashboards as JSON files."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []

    for dash in dashboards:
        data = dash.to_grafana()
        filepath = out / f"{dash.uid}.json"
        filepath.write_text(json.dumps(data, indent=2), encoding='utf-8')
        paths.append(str(filepath))

    return paths


def export_json_report(output: ForgeOutput, filepath: str) -> str:
    """Export full report as JSON."""
    data = {
        "services_processed": output.services_processed,
        "alert_groups": len(output.alert_groups),
        "total_rules": output.total_rules,
        "total_panels": output.total_panels,
        "groups": [
            {
                "name": g.name,
                "rule_count": g.rule_count,
                "rules": [
                    {"name": r.name, "severity": r.severity.value, "expr": r.expr[:100]}
                    for r in g.rules
                ],
            }
            for g in output.alert_groups
        ],
    }
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    return str(path)
