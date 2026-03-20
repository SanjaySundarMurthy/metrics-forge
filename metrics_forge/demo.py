"""Demo project generator for metrics-forge."""

from pathlib import Path
import yaml


def create_demo_project(output_dir: str = "demo-metrics") -> str:
    """Create demo service definitions."""
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    services = {
        "services": [
            {
                "name": "api-gateway",
                "tier": "critical",
                "namespace": "production",
                "port": 8080,
                "team": "platform",
                "description": "Main API gateway handling all external traffic",
                "slos": [
                    {"type": "availability", "target": 99.95, "window": "30d"},
                    {"type": "latency", "target": 200, "window": "30d", "description": "p99 < 200ms"},
                    {"type": "error_rate", "target": 99.9, "window": "7d"},
                ],
                "labels": {"app": "api-gateway", "env": "production"},
            },
            {
                "name": "user-service",
                "tier": "standard",
                "namespace": "production",
                "port": 8081,
                "team": "accounts",
                "description": "User management microservice",
                "slos": [
                    {"type": "availability", "target": 99.9, "window": "30d"},
                    {"type": "latency", "target": 500, "window": "30d"},
                ],
                "labels": {"app": "user-service", "env": "production"},
            },
            {
                "name": "notification-worker",
                "tier": "best_effort",
                "namespace": "workers",
                "port": 9090,
                "team": "messaging",
                "description": "Async notification processor",
                "slos": [
                    {"type": "availability", "target": 99.0},
                ],
                "labels": {"app": "notification-worker", "env": "production"},
            },
        ],
    }

    (root / "services.yaml").write_text(
        yaml.dump(services, default_flow_style=False, sort_keys=False), encoding='utf-8'
    )

    return str(root)
