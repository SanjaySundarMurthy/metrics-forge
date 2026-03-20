"""Rule validator — validates generated and existing Prometheus rules."""

from ..models import (
    AlertRule, AlertGroup, AlertSeverity,
    RuleIssue, ValidationResult,
)

VALIDATION_RULES = {
    "MET-001": {"message": "Alert missing summary annotation", "severity": AlertSeverity.WARNING},
    "MET-002": {"message": "Alert missing description annotation", "severity": AlertSeverity.WARNING},
    "MET-003": {"message": "Alert missing severity label", "severity": AlertSeverity.CRITICAL},
    "MET-004": {"message": "Alert duration too short (<1m) for production", "severity": AlertSeverity.WARNING},
    "MET-005": {"message": "Alert missing runbook URL", "severity": AlertSeverity.INFO},
    "MET-006": {"message": "Duplicate alert name in group", "severity": AlertSeverity.CRITICAL},
    "MET-007": {"message": "Empty PromQL expression", "severity": AlertSeverity.CRITICAL},
    "MET-008": {"message": "Alert missing service label", "severity": AlertSeverity.WARNING},
    "MET-009": {"message": "Group has no rules", "severity": AlertSeverity.WARNING},
    "MET-010": {"message": "Alert name contains spaces or special characters", "severity": AlertSeverity.WARNING},
}


def validate_rules(groups: list[AlertGroup]) -> ValidationResult:
    """Validate alert rule groups."""
    all_issues = []
    rules_checked = 0

    for group in groups:
        # MET-009: Empty group
        if not group.rules:
            all_issues.append(RuleIssue(
                rule_id="MET-009",
                message=VALIDATION_RULES["MET-009"]["message"],
                severity=VALIDATION_RULES["MET-009"]["severity"],
                service=group.name,
            ))
            continue

        seen_names: set[str] = set()
        for rule in group.rules:
            rules_checked += 1
            issues = _validate_rule(rule, seen_names)
            all_issues.extend(issues)

    return ValidationResult(issues=all_issues, rules_checked=rules_checked)


def _validate_rule(rule: AlertRule, seen_names: set) -> list[RuleIssue]:
    """Validate a single alert rule."""
    issues = []

    # MET-001: Missing summary
    if not rule.summary:
        issues.append(RuleIssue(
            rule_id="MET-001",
            message=VALIDATION_RULES["MET-001"]["message"],
            severity=VALIDATION_RULES["MET-001"]["severity"],
            service=rule.labels.get("service", ""),
            suggestion="Add a summary annotation to the alert rule",
        ))

    # MET-002: Missing description
    if not rule.description:
        issues.append(RuleIssue(
            rule_id="MET-002",
            message=VALIDATION_RULES["MET-002"]["message"],
            severity=VALIDATION_RULES["MET-002"]["severity"],
            service=rule.labels.get("service", ""),
        ))

    # MET-003: Missing severity
    if "severity" not in rule.labels and rule.severity is None:
        issues.append(RuleIssue(
            rule_id="MET-003",
            message=VALIDATION_RULES["MET-003"]["message"],
            severity=VALIDATION_RULES["MET-003"]["severity"],
        ))

    # MET-004: Duration too short
    duration_str = rule.duration.rstrip('m').rstrip('s')
    try:
        if rule.duration.endswith('s') and int(duration_str) < 60:
            issues.append(RuleIssue(
                rule_id="MET-004",
                message=VALIDATION_RULES["MET-004"]["message"],
                severity=VALIDATION_RULES["MET-004"]["severity"],
                suggestion="Use at least 1m for production alerts",
            ))
    except ValueError:
        pass

    # MET-005: Missing runbook
    if not rule.runbook_url:
        issues.append(RuleIssue(
            rule_id="MET-005",
            message=VALIDATION_RULES["MET-005"]["message"],
            severity=VALIDATION_RULES["MET-005"]["severity"],
        ))

    # MET-006: Duplicate name
    if rule.name in seen_names:
        issues.append(RuleIssue(
            rule_id="MET-006",
            message=f"Duplicate alert name: '{rule.name}'",
            severity=VALIDATION_RULES["MET-006"]["severity"],
        ))
    seen_names.add(rule.name)

    # MET-007: Empty expression
    if not rule.expr.strip():
        issues.append(RuleIssue(
            rule_id="MET-007",
            message=VALIDATION_RULES["MET-007"]["message"],
            severity=VALIDATION_RULES["MET-007"]["severity"],
        ))

    # MET-008: Missing service label
    if "service" not in rule.labels:
        issues.append(RuleIssue(
            rule_id="MET-008",
            message=VALIDATION_RULES["MET-008"]["message"],
            severity=VALIDATION_RULES["MET-008"]["severity"],
        ))

    # MET-010: Invalid name
    import re
    if re.search(r'[^a-zA-Z0-9_]', rule.name):
        issues.append(RuleIssue(
            rule_id="MET-010",
            message=VALIDATION_RULES["MET-010"]["message"],
            severity=VALIDATION_RULES["MET-010"]["severity"],
            suggestion="Use snake_case for alert names",
        ))

    return issues
