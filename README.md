# metrics-forge

[![CI](https://github.com/SanjaySundarMurthy/metrics-forge/actions/workflows/ci.yml/badge.svg)](https://github.com/SanjaySundarMurthy/metrics-forge/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/metrics-forge)](https://pypi.org/project/metrics-forge/)
[![PyPI](https://img.shields.io/pypi/v/metrics-forge)](https://pypi.org/project/metrics-forge/)

**Generate Prometheus alerting rules and Grafana dashboards from service definitions.**

Define services with SLOs in YAML, and metrics-forge generates production-ready Prometheus alert rules and Grafana dashboards automatically.

## Features

- **Rule Generation** — Standard + SLO-based Prometheus alert rules per service tier
- **Dashboard Generation** — Grafana dashboards with request rate, latency, CPU, memory, pod panels
- **Service Tiers** — Critical, Standard, Best Effort with adjusted thresholds and durations
- **SLO Support** — Availability, Latency, Error Rate with burn rate alerting
- **Rule Validation** — 10 rules (MET-001 to MET-010) for alert quality
- **Multi-Format Export** — Prometheus YAML, Grafana JSON, report JSON

## Installation

```bash
pip install metrics-forge
```

## Quick Start

```bash
metrics-forge demo
metrics-forge generate demo-metrics/services.yaml
metrics-forge generate demo-metrics/services.yaml -o rules.yaml -d dashboards/
metrics-forge validate demo-metrics/services.yaml
metrics-forge rules
```

## Command Reference

### `metrics-forge generate`

Generate Prometheus alerting rules and Grafana dashboards from service definitions.

```bash
metrics-forge generate <service-file> [OPTIONS]

Options:
  --format [text|json]      Output format (default: text)
  --output-dir DIR          Output directory for generated files
  --type [alerts|dashboards|all]  What to generate (default: all)
```

### `metrics-forge validate`

Validate generated rules against best practices.

```bash
metrics-forge validate <rules-file> [OPTIONS]

Options:
  --format [text|json]    Output format
  --fail-on [SEVERITY]    Exit with code 1 if findings at this level
```

### `metrics-forge demo`

Generate sample service definitions to get started.

```bash
metrics-forge demo
```

### `metrics-forge rules`

Display all validation rules.

```bash
metrics-forge rules
```

## Sample Output

```
metrics-forge v1.0.0 - Observability Config Generator

Processing: services.yaml
Services found: 4

Generating Prometheus alerts...
  ✓ api-gateway: 6 alert rules generated
  ✓ auth-service: 5 alert rules generated
  ✓ payment-service: 7 alert rules generated (SLO-aware)
  ✓ notification-service: 4 alert rules generated

Generating Grafana dashboards...
  ✓ api-gateway: dashboard with 8 panels
  ✓ auth-service: dashboard with 6 panels
  ✓ payment-service: dashboard with 10 panels
  ✓ notification-service: dashboard with 5 panels

Output: ./generated/
  alerts/prometheus-rules.yml (22 rules)
  dashboards/api-gateway.json
  dashboards/auth-service.json
  dashboards/payment-service.json
  dashboards/notification-service.json
```

## Service Definition Format

```yaml
services:
  - name: api-gateway
    type: http
    slo:
      availability: 99.9
      latency_p99_ms: 200
    metrics:
      - request_rate
      - error_rate
      - latency
      - saturation
```

## Testing

```bash
pip install -e ".[dev]"
pytest -v
ruff check .
```

## License

MIT

---

## Author

**Sanjay S** — [GitHub](https://github.com/SanjaySundarMurthy)


## 🐳 Docker

Run without installing Python:

```bash
# Build the image
docker build -t metrics-forge .

# Run
docker run --rm metrics-forge --help

# Example with volume mount
docker run --rm -v ${PWD}:/workspace metrics-forge [command] /workspace
```

Or pull from the container registry:

```bash
docker pull ghcr.io/SanjaySundarMurthy/metrics-forge:latest
docker run --rm ghcr.io/SanjaySundarMurthy/metrics-forge:latest --help
```

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

Please ensure tests pass before submitting:

```bash
pip install metrics-forge
pytest -v
ruff check .
```

## 🔗 Links

- **PyPI**: [https://pypi.org/project/metrics-forge/](https://pypi.org/project/metrics-forge/)
- **GitHub**: [https://github.com/SanjaySundarMurthy/metrics-forge](https://github.com/SanjaySundarMurthy/metrics-forge)
- **Issues**: [https://github.com/SanjaySundarMurthy/metrics-forge/issues](https://github.com/SanjaySundarMurthy/metrics-forge/issues)