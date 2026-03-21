"""Domain models for metrics generation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ServiceTier(Enum):
    CRITICAL = "critical"
    STANDARD = "standard"
    BEST_EFFORT = "best_effort"


class AlertSeverity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class SLOType(Enum):
    AVAILABILITY = "availability"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


class PanelType(Enum):
    GRAPH = "graph"
    STAT = "stat"
    TABLE = "table"
    GAUGE = "gauge"
    HEATMAP = "heatmap"


@dataclass
class SLOSpec:
    slo_type: SLOType
    target: float  # e.g., 99.9
    window: str = "30d"
    description: str = ""

    @property
    def error_budget(self) -> float:
        return 100.0 - self.target


@dataclass
class AlertRule:
    name: str
    expr: str
    duration: str = "5m"
    severity: AlertSeverity = AlertSeverity.WARNING
    summary: str = ""
    description: str = ""
    labels: dict = field(default_factory=dict)
    annotations: dict = field(default_factory=dict)
    runbook_url: str = ""

    def to_prometheus(self) -> dict:
        rule: dict[str, Any] = {
            "alert": self.name,
            "expr": self.expr,
            "for": self.duration,
            "labels": {**self.labels, "severity": self.severity.value},
            "annotations": {**self.annotations},
        }
        if self.summary:
            rule["annotations"]["summary"] = self.summary
        if self.description:
            rule["annotations"]["description"] = self.description
        if self.runbook_url:
            rule["annotations"]["runbook_url"] = self.runbook_url
        return rule


@dataclass
class AlertGroup:
    name: str
    rules: list[AlertRule] = field(default_factory=list)
    interval: str = "30s"

    def to_prometheus(self) -> dict:
        return {
            "name": self.name,
            "interval": self.interval,
            "rules": [r.to_prometheus() for r in self.rules],
        }

    @property
    def rule_count(self) -> int:
        return len(self.rules)


@dataclass
class GrafanaPanel:
    title: str
    panel_type: PanelType
    expr: str
    description: str = ""
    unit: str = ""
    thresholds: list = field(default_factory=list)

    def to_grafana(self, panel_id: int, grid_x: int, grid_y: int) -> dict:
        panel: dict[str, Any] = {
            "id": panel_id,
            "title": self.title,
            "type": self.panel_type.value,
            "gridPos": {"h": 8, "w": 12, "x": grid_x, "y": grid_y},
            "targets": [{"expr": self.expr, "refId": "A"}],
        }
        if self.description:
            panel["description"] = self.description
        if self.unit:
            panel.setdefault("fieldConfig", {}).setdefault("defaults", {})["unit"] = self.unit
        return panel


@dataclass
class GrafanaDashboard:
    title: str
    panels: list[GrafanaPanel] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    refresh: str = "30s"
    uid: str = ""

    def to_grafana(self) -> dict:
        panel_list = []
        for i, p in enumerate(self.panels):
            grid_x = (i % 2) * 12
            grid_y = (i // 2) * 8
            panel_list.append(p.to_grafana(i + 1, grid_x, grid_y))

        return {
            "dashboard": {
                "title": self.title,
                "uid": self.uid or self.title.lower().replace(" ", "-"),
                "tags": self.tags,
                "refresh": self.refresh,
                "panels": panel_list,
                "schemaVersion": 39,
                "version": 1,
            },
        }

    @property
    def panel_count(self) -> int:
        return len(self.panels)


@dataclass
class ServiceDefinition:
    name: str
    tier: ServiceTier = ServiceTier.STANDARD
    namespace: str = "default"
    port: int = 8080
    slos: list[SLOSpec] = field(default_factory=list)
    custom_metrics: list[str] = field(default_factory=list)
    labels: dict = field(default_factory=dict)
    team: str = ""
    description: str = ""


@dataclass
class ForgeOutput:
    alert_groups: list[AlertGroup] = field(default_factory=list)
    dashboards: list[GrafanaDashboard] = field(default_factory=list)
    services_processed: int = 0

    @property
    def total_rules(self) -> int:
        return sum(g.rule_count for g in self.alert_groups)

    @property
    def total_panels(self) -> int:
        return sum(d.panel_count for d in self.dashboards)


@dataclass
class RuleIssue:
    rule_id: str
    message: str
    severity: AlertSeverity
    service: str = ""
    suggestion: str = ""


@dataclass
class ValidationResult:
    issues: list[RuleIssue] = field(default_factory=list)
    rules_checked: int = 0

    @property
    def passed(self) -> bool:
        return not any(i.severity == AlertSeverity.CRITICAL for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == AlertSeverity.CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == AlertSeverity.WARNING)
