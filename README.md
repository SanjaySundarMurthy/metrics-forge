# metrics-forge

[![CI](https://github.com/SanjaySundarMurthy/metrics-forge/actions/workflows/ci.yml/badge.svg)](https://github.com/SanjaySundarMurthy/metrics-forge/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/metrics-forge)](https://pypi.org/project/metrics-forge/)
[![PyPI](https://img.shields.io/pypi/v/metrics-forge)](https://pypi.org/project/metrics-forge/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Generate production-ready Prometheus alerting rules and Grafana dashboards from service definitions.**

Define services with SLOs in YAML, and metrics-forge generates Prometheus alert rules with burn rate alerting, Grafana dashboards with standard panels, and validates rules against best practices — all automatically.

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Rule Generation** | Standard + SLO-based Prometheus alert rules per service tier |
| **Dashboard Generation** | Grafana dashboards with request rate, latency, CPU, memory, pod panels |
| **Service Tiers** | Critical, Standard, Best Effort with adjusted thresholds and durations |
| **SLO Support** | Availability, Latency, Error Rate with multi-window burn rate alerting |
| **Rule Validation** | 10 validation rules (MET-001 to MET-010) for alert quality |
| **Rule Diffing** | Compare generated rules with existing Prometheus rules |
| **Custom Metrics** | Support for custom application metrics |
| **Multi-Format Export** | Prometheus YAML, Grafana JSON, JSON reports |

## 📦 Installation

```bash
pip install metrics-forge
```

For development:

```bash
pip install -e ".[dev]"
```

## 🚀 Quick Start

```bash
# Create demo service definitions
metrics-forge demo

# Generate alerts and dashboards
metrics-forge generate demo-metrics/services.yaml

# Export to files
metrics-forge generate demo-metrics/services.yaml -o rules.yaml -d dashboards/

# Validate rules
metrics-forge validate demo-metrics/services.yaml

# List validation rules
metrics-forge rules

# Compare with existing rules
metrics-forge diff demo-metrics/services.yaml existing-rules.yaml
```

## 📖 Command Reference

### `metrics-forge generate`

Generate Prometheus alerting rules and Grafana dashboards from service definitions.

```bash
metrics-forge generate <service-file> [OPTIONS]

Options:
  -o, --output PATH         Output YAML file for Prometheus rules
  -d, --dashboard-dir DIR   Output directory for Grafana dashboards
  --format [text|json]      Output format (default: text)
  --type [alerts|dashboards|all]  What to generate (default: all)
```

**Examples:**

```bash
# Generate and display
metrics-forge generate services.yaml

# Generate only alerts
metrics-forge generate services.yaml --type alerts -o alerts.yaml

# Generate only dashboards
metrics-forge generate services.yaml --type dashboards -d dashboards/

# Export as JSON report
metrics-forge generate services.yaml --format json -o report.json
```

### `metrics-forge validate`

Validate generated rules against best practices (10 rules).

```bash
metrics-forge validate <services-file> [OPTIONS]

Options:
  --format [text|json]      Output format (default: text)
  --fail-on [critical|warning]  Exit with code 1 if issues at this level
```

**Examples:**

```bash
# Validate and display
metrics-forge validate services.yaml

# Fail CI on critical issues
metrics-forge validate services.yaml --fail-on critical

# Output as JSON for automation
metrics-forge validate services.yaml --format json
```

### `metrics-forge diff`

Compare generated rules with existing Prometheus rules to detect drift.

```bash
metrics-forge diff <services-file> <existing-rules-file> [OPTIONS]

Options:
  --format [text|json]      Output format (default: text)
```

### `metrics-forge demo`

Generate sample service definitions to get started.

```bash
metrics-forge demo [OPTIONS]

Options:
  -o, --output-dir DIR      Output directory (default: demo-metrics)
```

### `metrics-forge rules`

Display all 10 validation rules with severities.

```bash
metrics-forge rules
```

## 📋 Service Definition Format

```yaml
services:
  - name: api-gateway
    tier: critical          # critical | standard | best_effort
    namespace: production
    port: 8080
    team: platform
    description: Main API gateway handling all external traffic
    slos:
      - type: availability
        target: 99.95       # 99.95% availability target
        window: 30d
      - type: latency
        target: 200         # p99 < 200ms
        window: 30d
      - type: error_rate
        target: 99.9        # < 0.1% error rate
        window: 7d
    custom_metrics:
      - cache_hit_ratio
      - queue_depth
    labels:
      app: api-gateway
      env: production
```

## 🎯 Service Tiers

| Tier | Fast Duration | Medium Duration | Slow Duration | Use Case |
|------|---------------|-----------------|---------------|----------|
| **Critical** | 1m | 5m | 15m | User-facing, revenue-critical |
| **Standard** | 5m | 10m | 30m | Internal services, APIs |
| **Best Effort** | 10m | 15m | 1h | Background workers, batch jobs |

## 📊 Generated Alert Rules

For each service, metrics-forge generates:

| Alert | Description | Severity |
|-------|-------------|----------|
| `{service}_high_error_rate` | HTTP 5xx error rate > 5% | CRITICAL (tier-dependent) |
| `{service}_high_latency_p99` | p99 latency > 1s | WARNING |
| `{service}_pod_restarts` | > 3 restarts in 1h | WARNING |
| `{service}_high_cpu` | CPU usage > 85% | WARNING |
| `{service}_high_memory` | Memory usage > 85% | WARNING |
| `{service}_pod_not_ready` | Pod not in ready state | CRITICAL (tier-dependent) |

**SLO-based alerts** (when SLOs defined):

| Alert | Description | Severity |
|-------|-------------|----------|
| `{service}_slo_availability_fast_burn` | 14.4x burn rate (2m window) | CRITICAL |
| `{service}_slo_availability_slow_burn` | 3x burn rate (15m window) | WARNING |
| `{service}_slo_latency` | p99 latency exceeds target | WARNING |
| `{service}_slo_error_rate` | Error rate exceeds threshold | CRITICAL |

## 📈 Generated Dashboard Panels

Each Grafana dashboard includes:

- **Request Rate** — HTTP requests per second by status code
- **Error Rate** — Current error percentage
- **Request Latency** — p99 latency graph
- **CPU Usage** — Container CPU by pod
- **Memory Usage** — Memory working set by pod
- **Pod Restarts** — Restart count in last hour
- **Running Pods** — Ready pod count
- **Availability SLO** — SLO gauge (when availability SLO defined)

## ✅ Validation Rules

| Rule ID | Severity | Description |
|---------|----------|-------------|
| MET-001 | WARNING | Alert missing summary annotation |
| MET-002 | WARNING | Alert missing description annotation |
| MET-003 | CRITICAL | Alert missing severity label |
| MET-004 | WARNING | Alert duration too short (<1m) for production |
| MET-005 | INFO | Alert missing runbook URL |
| MET-006 | CRITICAL | Duplicate alert name in group |
| MET-007 | CRITICAL | Empty PromQL expression |
| MET-008 | WARNING | Alert missing service label |
| MET-009 | WARNING | Group has no rules |
| MET-010 | WARNING | Alert name contains spaces or special characters |

## 📁 Project Structure

```
metrics-forge/
├── metrics_forge/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point (Click)
│   ├── demo.py             # Demo project generator
│   ├── models.py           # Domain models (dataclasses)
│   ├── parser.py           # YAML service definition parser
│   ├── analyzers/
│   │   ├── rule_generator.py      # Prometheus rule generation
│   │   ├── dashboard_generator.py # Grafana dashboard generation
│   │   └── rule_validator.py      # Validation rules engine
│   └── reporters/
│       ├── terminal_reporter.py   # Rich terminal output
│       └── export_reporter.py     # YAML/JSON export
├── tests/
│   ├── conftest.py         # Pytest fixtures
│   ├── test_analyzers.py   # Generator & validator tests
│   ├── test_cli.py         # CLI command tests
│   └── test_models.py      # Model tests
├── pyproject.toml
├── Dockerfile
└── README.md
```

## 🐳 Docker

Run without installing Python:

```bash
# Build the image
docker build -t metrics-forge .

# Run commands
docker run --rm metrics-forge --help
docker run --rm metrics-forge demo
docker run --rm -v ${PWD}:/workspace metrics-forge generate /workspace/services.yaml
```

Or pull from the container registry:

```bash
docker pull ghcr.io/SanjaySundarMurthy/metrics-forge:latest
docker run --rm ghcr.io/SanjaySundarMurthy/metrics-forge:latest --help
```

## 🧪 Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Run linter
ruff check .

# Run tests with coverage
pytest --cov=metrics_forge
```

**Test Count:** 47 tests covering CLI, analyzers, models, and validators.

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

Please ensure tests pass before submitting:

```bash
pytest -v
ruff check .
```

## 📄 License

MIT

## 👤 Author

**Sanjay S** — [GitHub](https://github.com/SanjaySundarMurthy)

## 🔗 Links

- **PyPI**: [https://pypi.org/project/metrics-forge/](https://pypi.org/project/metrics-forge/)
- **GitHub**: [https://github.com/SanjaySundarMurthy/metrics-forge](https://github.com/SanjaySundarMurthy/metrics-forge)
- **Issues**: [https://github.com/SanjaySundarMurthy/metrics-forge/issues](https://github.com/SanjaySundarMurthy/metrics-forge/issues)
