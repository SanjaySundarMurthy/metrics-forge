"""Dashboard generator — creates Grafana dashboards from service definitions."""

from ..models import (
    ServiceDefinition, ServiceTier, GrafanaPanel, GrafanaDashboard,
    PanelType, ForgeOutput,
)


def generate_dashboards(services: list[ServiceDefinition]) -> list[GrafanaDashboard]:
    """Generate Grafana dashboards for all services."""
    dashboards = []

    for svc in services:
        panels = _generate_panels(svc)
        dashboard = GrafanaDashboard(
            title=f"{svc.name} - Service Dashboard",
            panels=panels,
            tags=["auto-generated", svc.tier.value, svc.namespace],
            uid=f"{svc.namespace}-{svc.name}",
        )
        dashboards.append(dashboard)

    return dashboards


def _generate_panels(svc: ServiceDefinition) -> list[GrafanaPanel]:
    """Generate dashboard panels for a service."""
    panels = []
    ns = svc.namespace
    name = svc.name

    # Request rate
    panels.append(GrafanaPanel(
        title="Request Rate",
        panel_type=PanelType.GRAPH,
        expr=f'sum(rate(http_requests_total{{namespace="{ns}",service="{name}"}}[5m])) by (code)',
        description="HTTP request rate by status code",
        unit="reqps",
    ))

    # Error rate
    panels.append(GrafanaPanel(
        title="Error Rate (%)",
        panel_type=PanelType.STAT,
        expr=f'sum(rate(http_requests_total{{namespace="{ns}",service="{name}",code=~"5.."}}[5m])) / sum(rate(http_requests_total{{namespace="{ns}",service="{name}"}}[5m])) * 100',
        description="Current error rate percentage",
        unit="percent",
    ))

    # Latency p50/p95/p99
    panels.append(GrafanaPanel(
        title="Request Latency",
        panel_type=PanelType.GRAPH,
        expr=f'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{{namespace="{ns}",service="{name}"}}[5m])) by (le))',
        description="Request latency percentiles",
        unit="s",
    ))

    # CPU usage
    panels.append(GrafanaPanel(
        title="CPU Usage",
        panel_type=PanelType.GRAPH,
        expr=f'sum(rate(container_cpu_usage_seconds_total{{namespace="{ns}",container="{name}"}}[5m])) by (pod)',
        description="CPU usage by pod",
        unit="cores",
    ))

    # Memory usage
    panels.append(GrafanaPanel(
        title="Memory Usage",
        panel_type=PanelType.GRAPH,
        expr=f'sum(container_memory_working_set_bytes{{namespace="{ns}",container="{name}"}}) by (pod)',
        description="Memory working set by pod",
        unit="bytes",
    ))

    # Pod restarts
    panels.append(GrafanaPanel(
        title="Pod Restarts",
        panel_type=PanelType.STAT,
        expr=f'sum(increase(kube_pod_container_status_restarts_total{{namespace="{ns}",container="{name}"}}[1h]))',
        description="Pod restarts in the last hour",
    ))

    # Pod count
    panels.append(GrafanaPanel(
        title="Running Pods",
        panel_type=PanelType.STAT,
        expr=f'count(kube_pod_status_ready{{namespace="{ns}",condition="true",pod=~"{name}.*"}})',
        description="Number of ready pods",
    ))

    # Availability (if SLO defined)
    if any(s.slo_type.value == "availability" for s in svc.slos):
        panels.append(GrafanaPanel(
            title="Availability SLO",
            panel_type=PanelType.GAUGE,
            expr=f'sum(rate(http_requests_total{{namespace="{ns}",service="{name}",code!~"5.."}}[1h])) / sum(rate(http_requests_total{{namespace="{ns}",service="{name}"}}[1h])) * 100',
            description="Current availability percentage",
            unit="percent",
        ))

    return panels
