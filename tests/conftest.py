"""Shared fixtures for metrics-forge tests."""

import pytest

from metrics_forge.models import (
    AlertGroup,
    AlertRule,
    AlertSeverity,
    ServiceDefinition,
    ServiceTier,
    SLOSpec,
    SLOType,
)


@pytest.fixture
def critical_service():
    return ServiceDefinition(
        name="api-gateway",
        tier=ServiceTier.CRITICAL,
        namespace="production",
        port=8080,
        team="platform",
        slos=[
            SLOSpec(slo_type=SLOType.AVAILABILITY, target=99.95),
            SLOSpec(slo_type=SLOType.LATENCY, target=200),
            SLOSpec(slo_type=SLOType.ERROR_RATE, target=99.9),
        ],
    )


@pytest.fixture
def standard_service():
    return ServiceDefinition(
        name="user-service",
        tier=ServiceTier.STANDARD,
        namespace="production",
        team="accounts",
        slos=[SLOSpec(slo_type=SLOType.AVAILABILITY, target=99.9)],
    )


@pytest.fixture
def best_effort_service():
    return ServiceDefinition(
        name="worker",
        tier=ServiceTier.BEST_EFFORT,
        namespace="workers",
    )


@pytest.fixture
def sample_rule():
    return AlertRule(
        name="test_high_error_rate",
        expr='rate(errors[5m]) > 0.05',
        severity=AlertSeverity.WARNING,
        summary="High error rate",
        description="Error rate above 5%",
        labels={"service": "test"},
    )


@pytest.fixture
def sample_group(sample_rule):
    return AlertGroup(name="test-alerts", rules=[sample_rule])


@pytest.fixture
def demo_dir(tmp_path):
    from metrics_forge.demo import create_demo_project
    return create_demo_project(str(tmp_path / "demo"))
