# metrics-forge

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
pip install -e .
```

## Quick Start

```bash
metrics-forge demo
metrics-forge generate demo-metrics/services.yaml
metrics-forge generate demo-metrics/services.yaml -o rules.yaml -d dashboards/
metrics-forge validate demo-metrics/services.yaml
metrics-forge rules
```

## Testing

```bash
python -m pytest tests/ -v
```

## License

MIT
