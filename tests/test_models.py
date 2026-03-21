"""Tests for domain models."""

from metrics_forge.models import (
    AlertRule,
    AlertSeverity,
    ForgeOutput,
    GrafanaDashboard,
    GrafanaPanel,
    PanelType,
    RuleIssue,
    SLOSpec,
    SLOType,
    ValidationResult,
)


class TestSLOSpec:
    def test_error_budget(self):
        slo = SLOSpec(slo_type=SLOType.AVAILABILITY, target=99.9)
        assert abs(slo.error_budget - 0.1) < 0.001

    def test_error_budget_high_target(self):
        slo = SLOSpec(slo_type=SLOType.AVAILABILITY, target=99.99)
        assert abs(slo.error_budget - 0.01) < 0.001


class TestAlertRule:
    def test_to_prometheus(self, sample_rule):
        result = sample_rule.to_prometheus()
        assert result["alert"] == "test_high_error_rate"
        assert result["expr"] == 'rate(errors[5m]) > 0.05'
        assert result["labels"]["severity"] == "warning"
        assert result["annotations"]["summary"] == "High error rate"

    def test_to_prometheus_with_runbook(self):
        rule = AlertRule(name="test", expr="up == 0", runbook_url="https://wiki/test")
        result = rule.to_prometheus()
        assert result["annotations"]["runbook_url"] == "https://wiki/test"


class TestAlertGroup:
    def test_rule_count(self, sample_group):
        assert sample_group.rule_count == 1

    def test_to_prometheus(self, sample_group):
        result = sample_group.to_prometheus()
        assert result["name"] == "test-alerts"
        assert len(result["rules"]) == 1


class TestGrafanaPanel:
    def test_to_grafana(self):
        panel = GrafanaPanel(title="Test", panel_type=PanelType.GRAPH, expr="up")
        result = panel.to_grafana(1, 0, 0)
        assert result["title"] == "Test"
        assert result["type"] == "graph"
        assert result["targets"][0]["expr"] == "up"


class TestGrafanaDashboard:
    def test_to_grafana(self):
        panel = GrafanaPanel(title="P1", panel_type=PanelType.STAT, expr="up")
        dash = GrafanaDashboard(title="Test Dashboard", panels=[panel], tags=["test"])
        result = dash.to_grafana()
        assert result["dashboard"]["title"] == "Test Dashboard"
        assert len(result["dashboard"]["panels"]) == 1

    def test_panel_count(self):
        dash = GrafanaDashboard(title="T", panels=[
            GrafanaPanel(title="P1", panel_type=PanelType.STAT, expr="up"),
            GrafanaPanel(title="P2", panel_type=PanelType.GRAPH, expr="up"),
        ])
        assert dash.panel_count == 2


class TestForgeOutput:
    def test_totals(self, sample_group):
        output = ForgeOutput(alert_groups=[sample_group], services_processed=1)
        assert output.total_rules == 1

    def test_empty(self):
        output = ForgeOutput()
        assert output.total_rules == 0
        assert output.total_panels == 0


class TestValidationResult:
    def test_passed(self):
        result = ValidationResult(issues=[], rules_checked=5)
        assert result.passed is True

    def test_failed(self):
        result = ValidationResult(
            issues=[RuleIssue(rule_id="MET-003", message="test", severity=AlertSeverity.CRITICAL)],
            rules_checked=1,
        )
        assert result.passed is False
        assert result.error_count == 1
