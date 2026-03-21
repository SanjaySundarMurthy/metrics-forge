"""Tests for analyzers."""

from metrics_forge.analyzers.dashboard_generator import generate_dashboards
from metrics_forge.analyzers.rule_generator import generate_rules
from metrics_forge.analyzers.rule_validator import VALIDATION_RULES, validate_rules
from metrics_forge.models import (
    AlertGroup,
    AlertRule,
    AlertSeverity,
)


class TestRuleGenerator:
    def test_generate_critical_service(self, critical_service):
        output = generate_rules([critical_service])
        assert output.services_processed == 1
        assert len(output.alert_groups) == 1
        assert output.total_rules >= 6  # standard + SLO rules

    def test_critical_tier_severity(self, critical_service):
        output = generate_rules([critical_service])
        rules = output.alert_groups[0].rules
        error_rule = next(r for r in rules if "error_rate" in r.name and "slo" not in r.name)
        assert error_rule.severity == AlertSeverity.CRITICAL

    def test_standard_service(self, standard_service):
        output = generate_rules([standard_service])
        assert output.total_rules >= 6

    def test_best_effort_service(self, best_effort_service):
        output = generate_rules([best_effort_service])
        assert output.total_rules >= 6  # standard rules still generated

    def test_slo_availability_rules(self, critical_service):
        output = generate_rules([critical_service])
        rules = output.alert_groups[0].rules
        slo_rules = [r for r in rules if "slo_availability" in r.name]
        assert len(slo_rules) >= 2  # fast burn + slow burn

    def test_slo_latency_rule(self, critical_service):
        output = generate_rules([critical_service])
        rules = output.alert_groups[0].rules
        latency = [r for r in rules if "slo_latency" in r.name]
        assert len(latency) >= 1

    def test_empty_services(self):
        output = generate_rules([])
        assert output.total_rules == 0

    def test_rules_have_labels(self, critical_service):
        output = generate_rules([critical_service])
        for rule in output.alert_groups[0].rules:
            assert "service" in rule.labels

    def test_multiple_services(self, critical_service, standard_service):
        output = generate_rules([critical_service, standard_service])
        assert len(output.alert_groups) == 2


class TestDashboardGenerator:
    def test_generate_dashboard(self, critical_service):
        dashboards = generate_dashboards([critical_service])
        assert len(dashboards) == 1
        assert dashboards[0].panel_count >= 7

    def test_availability_slo_panel(self, critical_service):
        dashboards = generate_dashboards([critical_service])
        titles = [p.title for p in dashboards[0].panels]
        assert "Availability SLO" in titles

    def test_no_slo_panel_without_slo(self, best_effort_service):
        dashboards = generate_dashboards([best_effort_service])
        titles = [p.title for p in dashboards[0].panels]
        assert "Availability SLO" not in titles

    def test_multiple_services(self, critical_service, standard_service):
        dashboards = generate_dashboards([critical_service, standard_service])
        assert len(dashboards) == 2


class TestRuleValidator:
    def test_valid_rules(self, sample_group):
        result = validate_rules([sample_group])
        assert result.rules_checked == 1

    def test_empty_group(self):
        group = AlertGroup(name="empty")
        result = validate_rules([group])
        rule_ids = {i.rule_id for i in result.issues}
        assert "MET-009" in rule_ids

    def test_missing_summary(self):
        rule = AlertRule(name="test", expr="up==0", labels={"service": "x"})
        group = AlertGroup(name="g", rules=[rule])
        result = validate_rules([group])
        rule_ids = {i.rule_id for i in result.issues}
        assert "MET-001" in rule_ids

    def test_duplicate_name(self):
        r = AlertRule(name="dup", expr="up==0", summary="s", description="d", labels={"service": "x"})
        group = AlertGroup(name="g", rules=[r, r])
        result = validate_rules([group])
        rule_ids = {i.rule_id for i in result.issues}
        assert "MET-006" in rule_ids

    def test_empty_expr(self):
        rule = AlertRule(name="test", expr="", labels={"service": "x"})
        group = AlertGroup(name="g", rules=[rule])
        result = validate_rules([group])
        rule_ids = {i.rule_id for i in result.issues}
        assert "MET-007" in rule_ids

    def test_all_rules_defined(self):
        assert len(VALIDATION_RULES) == 10
        for i in range(1, 11):
            assert f"MET-{i:03d}" in VALIDATION_RULES
