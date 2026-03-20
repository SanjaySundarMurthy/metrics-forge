"""Parser for service definition YAML files."""

from pathlib import Path

import yaml

from .models import ServiceDefinition, ServiceTier, SLOSpec, SLOType


def parse_service_definitions(filepath: str) -> list[ServiceDefinition]:
    """Parse a YAML file containing service definitions."""
    path = Path(filepath)
    if not path.exists():
        return []

    data = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not data or 'services' not in data:
        return []

    services = []
    for svc_data in data['services']:
        slos = []
        for slo_data in svc_data.get('slos', []):
            slos.append(SLOSpec(
                slo_type=SLOType(slo_data['type']),
                target=float(slo_data['target']),
                window=slo_data.get('window', '30d'),
                description=slo_data.get('description', ''),
            ))

        services.append(ServiceDefinition(
            name=svc_data['name'],
            tier=ServiceTier(svc_data.get('tier', 'standard')),
            namespace=svc_data.get('namespace', 'default'),
            port=svc_data.get('port', 8080),
            slos=slos,
            custom_metrics=svc_data.get('custom_metrics', []),
            labels=svc_data.get('labels', {}),
            team=svc_data.get('team', ''),
            description=svc_data.get('description', ''),
        ))

    return services


def parse_existing_rules(filepath: str) -> list[dict]:
    """Parse existing Prometheus rule file."""
    path = Path(filepath)
    if not path.exists():
        return []

    data = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not data or 'groups' not in data:
        return []

    return data['groups']
