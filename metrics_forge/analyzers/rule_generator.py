"""Rule generator — creates Prometheus alert rules from service definitions."""

from ..models import (
    ServiceDefinition, ServiceTier, SLOSpec, SLOType,
    AlertRule, AlertGroup, AlertSeverity, ForgeOutput,
)

# Duration multipliers by service tier
TIER_DURATIONS = {
    ServiceTier.CRITICAL: {"fast": "1m", "medium": "5m", "slow": "15m"},
    ServiceTier.STANDARD: {"fast": "5m", "medium": "10m", "slow": "30m"},
    ServiceTier.BEST_EFFORT: {"fast": "10m", "medium": "15m", "slow": "1h"},
}


def generate_rules(services: list[ServiceDefinition]) -> ForgeOutput:
    """Generate Prometheus alert rules for all services."""
    output = ForgeOutput(services_processed=len(services))

    for svc in services:
        group = AlertGroup(name=f"{svc.name}-alerts")
        durations = TIER_DURATIONS.get(svc.tier, TIER_DURATIONS[ServiceTier.STANDARD])
        base_labels = {"service": svc.name, "namespace": svc.namespace}
        if svc.team:
            base_labels["team"] = svc.team

        # Standard rules for all services
        group.rules.extend(_generate_standard_rules(svc, durations, base_labels))

        # SLO-based rules
        for slo in svc.slos:
            group.rules.extend(_generate_slo_rules(svc, slo, durations, base_labels))

        output.alert_groups.append(group)

    return output


def _generate_standard_rules(svc: ServiceDefinition, durations: dict, labels: dict) -> list[AlertRule]:
    """Generate standard alerting rules for a service."""
    rules = []
    ns = svc.namespace
    name = svc.name

    # High error rate
    rules.append(AlertRule(
        name=f"{name}_high_error_rate",
        expr=f'sum(rate(http_requests_total{{namespace="{ns}",service="{name}",code=~"5.."}}[5m])) / sum(rate(http_requests_total{{namespace="{ns}",service="{name}"}}[5m])) > 0.05',
        duration=durations["fast"],
        severity=AlertSeverity.CRITICAL if svc.tier == ServiceTier.CRITICAL else AlertSeverity.WARNING,
        summary=f"High error rate on {name}",
        description=f"Error rate is above 5% for {name} in {ns}",
        labels=labels,
    ))

    # High latency (p99)
    rules.append(AlertRule(
        name=f"{name}_high_latency_p99",
        expr=f'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{{namespace="{ns}",service="{name}"}}[5m])) by (le)) > 1',
        duration=durations["medium"],
        severity=AlertSeverity.WARNING,
        summary=f"High p99 latency on {name}",
        description=f"p99 latency above 1s for {name} in {ns}",
        labels=labels,
    ))

    # Pod restarts
    rules.append(AlertRule(
        name=f"{name}_pod_restarts",
        expr=f'increase(kube_pod_container_status_restarts_total{{namespace="{ns}",container="{name}"}}[1h]) > 3',
        duration=durations["medium"],
        severity=AlertSeverity.WARNING,
        summary=f"Pod restarts detected for {name}",
        description=f"Container {name} has restarted more than 3 times in 1h",
        labels=labels,
    ))

    # High CPU
    rules.append(AlertRule(
        name=f"{name}_high_cpu",
        expr=f'sum(rate(container_cpu_usage_seconds_total{{namespace="{ns}",container="{name}"}}[5m])) / sum(kube_pod_container_resource_limits{{namespace="{ns}",container="{name}",resource="cpu"}}) > 0.85',
        duration=durations["slow"],
        severity=AlertSeverity.WARNING,
        summary=f"High CPU usage on {name}",
        description=f"CPU usage above 85% for {name}",
        labels=labels,
    ))

    # High memory
    rules.append(AlertRule(
        name=f"{name}_high_memory",
        expr=f'sum(container_memory_working_set_bytes{{namespace="{ns}",container="{name}"}}) / sum(kube_pod_container_resource_limits{{namespace="{ns}",container="{name}",resource="memory"}}) > 0.85',
        duration=durations["slow"],
        severity=AlertSeverity.WARNING,
        summary=f"High memory usage on {name}",
        description=f"Memory usage above 85% for {name}",
        labels=labels,
    ))

    # Pod not ready
    rules.append(AlertRule(
        name=f"{name}_pod_not_ready",
        expr=f'kube_pod_status_ready{{namespace="{ns}",condition="true",pod=~"{name}.*"}} == 0',
        duration=durations["medium"],
        severity=AlertSeverity.CRITICAL if svc.tier == ServiceTier.CRITICAL else AlertSeverity.WARNING,
        summary=f"Pod not ready: {name}",
        description=f"Pod {name} is not in ready state",
        labels=labels,
    ))

    return rules


def _generate_slo_rules(svc: ServiceDefinition, slo: SLOSpec, durations: dict, labels: dict) -> list[AlertRule]:
    """Generate SLO-based alerting rules."""
    rules = []
    name = svc.name
    ns = svc.namespace

    if slo.slo_type == SLOType.AVAILABILITY:
        budget = slo.error_budget / 100
        # Burn rate alert (fast burn)
        rules.append(AlertRule(
            name=f"{name}_slo_availability_fast_burn",
            expr=f'1 - (sum(rate(http_requests_total{{namespace="{ns}",service="{name}",code!~"5.."}}[5m])) / sum(rate(http_requests_total{{namespace="{ns}",service="{name}"}}[5m]))) > {budget * 14.4:.6f}',
            duration="2m",
            severity=AlertSeverity.CRITICAL,
            summary=f"SLO burn rate critical for {name}",
            description=f"Availability SLO ({slo.target}%) fast burn rate exceeded",
            labels={**labels, "slo": "availability"},
        ))
        # Slow burn
        rules.append(AlertRule(
            name=f"{name}_slo_availability_slow_burn",
            expr=f'1 - (sum(rate(http_requests_total{{namespace="{ns}",service="{name}",code!~"5.."}}[1h])) / sum(rate(http_requests_total{{namespace="{ns}",service="{name}"}}[1h]))) > {budget * 3:.6f}',
            duration="15m",
            severity=AlertSeverity.WARNING,
            summary=f"SLO slow burn for {name}",
            description=f"Availability SLO ({slo.target}%) slow burn rate exceeded",
            labels={**labels, "slo": "availability"},
        ))

    elif slo.slo_type == SLOType.LATENCY:
        threshold = slo.target / 1000  # target in ms, convert to seconds
        rules.append(AlertRule(
            name=f"{name}_slo_latency",
            expr=f'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{{namespace="{ns}",service="{name}"}}[5m])) by (le)) > {threshold}',
            duration=durations["fast"],
            severity=AlertSeverity.WARNING,
            summary=f"Latency SLO breached for {name}",
            description=f"p99 latency exceeds {slo.target}ms target",
            labels={**labels, "slo": "latency"},
        ))

    elif slo.slo_type == SLOType.ERROR_RATE:
        threshold = (100 - slo.target) / 100
        rules.append(AlertRule(
            name=f"{name}_slo_error_rate",
            expr=f'sum(rate(http_requests_total{{namespace="{ns}",service="{name}",code=~"5.."}}[5m])) / sum(rate(http_requests_total{{namespace="{ns}",service="{name}"}}[5m])) > {threshold}',
            duration=durations["fast"],
            severity=AlertSeverity.CRITICAL,
            summary=f"Error rate SLO breached for {name}",
            description=f"Error rate exceeds {100-slo.target}% threshold",
            labels={**labels, "slo": "error_rate"},
        ))

    return rules
